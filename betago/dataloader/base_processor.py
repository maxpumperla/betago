# This Source Code Form is subject to the terms of the Mozilla Public License,
# v. 2.0. If a copy of the MPL was not distributed with this file, You can
# obtain one at http://mozilla.org/MPL/2.0/.
from __future__ import print_function
from __future__ import absolute_import
import os
import gc
import glob
import os.path
import tarfile
import gzip
import shutil
import numpy as np
import argparse
import multiprocessing
from os import sys
from keras.utils import np_utils

from .. import gosgf
from .goboard import GoBoard
from .index_processor import KGSIndex
from .sampling import Sampler


def worker(jobinfo):
    try:
        clazz, dir_name, num_planes, zip_file, data_file_name, game_list = jobinfo
        clazz(dir_name, num_planes).process_zip(dir_name, zip_file, data_file_name, game_list)
    except (KeyboardInterrupt, SystemExit):
        raise Exception('>>> Exiting child process.')


class DataGenerator(object):
    def __init__(self, data_dir, samples):
        self.data_dir = data_dir
        self.files = set(file_name for file_name, index in samples)
        self.samples = samples
        self.num_samples = None

    def get_num_samples(self, batch_size=128, nb_classes=19 * 19):
        if self.num_samples is not None:
            return self.num_samples
        else:
            self.num_samples = 0
            for X, y in self._generate(batch_size=batch_size, nb_classes=nb_classes):
                self.num_samples += X.shape[0]
            return self.num_samples

    def _generate(self, batch_size, nb_classes):
        for zip_file_name in self.files:
            file_name = zip_file_name.replace('.tar.gz', '') + 'train'
            base = self.data_dir + '/' + file_name + '_features_*.npy'
            for feature_file in glob.glob(base):
                label_file = feature_file.replace('features', 'labels')
                X = np.load(feature_file)
                y = np.load(label_file)
                X = X.astype('float32')
                y = np_utils.to_categorical(y.astype(int), nb_classes)
                gc.collect()
                while X.shape[0] >= batch_size:
                    X_batch, X = X[:batch_size], X[batch_size:]
                    y_batch, y = y[:batch_size], y[batch_size:]
                    gc.collect()
                    yield X_batch, y_batch
            gc.collect()

    def generate(self, batch_size=128, nb_classes=19 * 19):
        while True:
            for item in self._generate(batch_size=batch_size, nb_classes=nb_classes):
                yield item


class GoBaseProcessor(object):
    '''
    Abstract base class for Go data processing. To implement this class, implement
    process_zip and consolidate_games below.

    Generally speaking, processing load is split between available CPUs, thereby generating intermediate
    files for each worker. Processing many files can produce massive amounts of data that will not (easily)
    fit into memory. To avoid overflow, deactivate file consolidation by initializing with consolidate=False.
    '''

    def __init__(self, data_directory='data', num_planes=7, consolidate=True):
        '''
        Parameters:
        -----------
        data_dir: relative path to store data files, defaults to 'data'
        num_planes: Number of Go board copies used as input, corresponds to the number of input channels
                    in a CNN.
        consolidate: Boolean flag to indicate if intermediate results should be consolidated into one, which
                     can be very expensive.
        '''
        self.data_dir = data_directory
        self.num_planes = num_planes
        self.consolidate = consolidate

    def process_zip(self, dir_name, zip_file_name, data_file_name, game_list):
        '''
        Method to determine how to process each zip file with games.
        '''
        return NotImplemented

    def consolidate_games(self, name, samples):
        '''
        Consolidate a list of results into one.
        '''
        return NotImplemented

    def load_go_data(self, types=['train'], data_dir='data', num_samples=1000):
        '''
        Main method to load go data.

        Loads and initializes an index from KGS and downloads zipped files. Depending on provided type, unzip and
        process data, then optionally store it in one consolidated file.

        Parameters:
        -----------
        types: Provide a list, subset of ['train', 'test'].
        data_dir: local folder to store data, provided as relative path.
        num_samples: Number of Go games to load.
        '''
        index = KGSIndex(data_directory=self.data_dir)
        index.download_files()

        for name in types:
            sampler = Sampler(data_dir=self.data_dir)
            if name == 'test':
                samples = sampler.test_games
            elif name == 'train' and num_samples is not None:
                samples = sampler.draw_training_samples(num_samples)
            elif name == 'train' and num_samples is None:
                samples = sampler.draw_all_training()

            # Map load to CPUs, then consolidate all examples
            self.map_to_workers(name, samples)

            # If consolidate flag is True, consolidate. Note that merging all data into, e.g.
            # one numpy array will be too expensive at some point.
            if self.consolidate:
                features_and_labels = self.consolidate_games(name, samples)
            else:
                print('>>> No consolidation done, single files stored in data folder')
        print('>>> Finished processing')
        if self.consolidate:
            return features_and_labels
        else:
            return

    def load_go_data_cli(self):
        '''
        Main method for loading Go game data from command line.
        Data types to choose from are:
            test: Load test data. This set is fixed and not contained in any train data.
            train: Load train data for specified number of games
        '''
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Process Go Game data')
        parser.add_argument('--type', dest='type', type=str, nargs='+',
                            help='Choose data type from test and train')
        parser.add_argument('--data', dest='data_dir', type=str, nargs='?',
                            help='Optional data directory')
        parser.add_argument('--n', dest='num_samples', type=int, nargs='?',
                            help='Number of samples used in training. If none provided, load full data set')
        args = parser.parse_args()

        # Determine data types for training
        types = args.type
        for t in types:
            if t not in ['test', 'train']:
                raise("""Unsupported type, choose from 'test', 'train' """)

        # Determine number of training samples
        num_samples = None if args.num_samples is None else args.num_samples

        # Determine local directory to put all data
        target_dir = 'data' if args.data_dir is None else args.data_dir
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)
        self.data_dir = target_dir

        self.load_go_data(types=types, data_dir=self.data_dir, num_samples=num_samples)

    def get_handicap(self, go_board, sgf):
        ''' Get handicap stones '''
        first_move_done = False
        if sgf.get_handicap() != None and sgf.get_handicap() != 0:
            for setup in sgf.get_root().get_setup_stones():
                for move in setup:
                    go_board.apply_move('b', move)
            first_move_done = True
        return go_board, first_move_done

    def map_to_workers(self, name, samples):
        '''
        Determine the list of zip files that need to be processed, then map load
        to number of available CPUs.
        '''
        # Create a dictionary with file names as keys and games as values
        zip_names = set()
        indices_by_zip_name = {}
        for filename, index in samples:
            zip_names.add(filename)
            if filename not in indices_by_zip_name:
                indices_by_zip_name[filename] = []
            indices_by_zip_name[filename].append(index)
        print('>>> Number of zip files: ' + str(len(zip_names)))

        # Transform the above dictionary to a list that can be processed in parallel
        zips_to_process = []
        for zip_name in zip_names:
            base_name = zip_name.replace('.tar.gz', '')
            data_file_name = base_name + name
            if not os.path.isfile(self.data_dir + '/' + data_file_name):
                zips_to_process.append((self.__class__, self.data_dir, self.num_planes, zip_name,
                                        data_file_name, indices_by_zip_name[zip_name]))

        # Determine number of CPU cores and split work load among them
        cores = multiprocessing.cpu_count()
        pool = multiprocessing.Pool(processes=cores)
        p = pool.map_async(worker, zips_to_process)
        try:
            results = p.get(0xFFFF)
            print(results)
        except KeyboardInterrupt:
            print("Caught KeyboardInterrupt, terminating workers")
            pool.terminate()
            pool.join()
            sys.exit(-1)

    def init_go_board(self, sgf_contents):
        ''' Initialize a 19x19 go board from SGF file content'''
        sgf = gosgf.Sgf_game.from_string(sgf_contents)
        return sgf, GoBoard(19)

    def num_total_examples(self, this_zip, game_list, name_list):
        ''' Total number of moves, i.e. training samples'''
        total_examples = 0
        for index in game_list:
            name = name_list[index + 1]
            if name.endswith('.sgf'):
                content = this_zip.extractfile(name).read()
                sgf, go_board_no_handy = self.init_go_board(content)
                go_board, first_move_done = self.get_handicap(go_board_no_handy, sgf)

                num_moves = 0
                for item in sgf.main_sequence_iter():
                    color, move = item.get_move()
                    if color is not None and move is not None:
                        if first_move_done:
                            num_moves = num_moves + 1
                        first_move_done = True
                total_examples = total_examples + num_moves
            else:
                raise ValueError(name + ' is not a valid sgf')
        return total_examples


class GoDataProcessor(GoBaseProcessor):
    '''
    GoDataProcessor generates data, e.g. numpy arrays, of features and labels and returns them to the user.
    '''
    def __init__(self, data_directory='data', num_planes=7, consolidate=True, use_generator=False):
        super(GoDataProcessor, self).__init__(data_directory=data_directory,
                                              num_planes=num_planes, consolidate=consolidate)
        self.use_generator = use_generator

    def feature_and_label(self, color, move, go_board):
        '''
        Given a go board and the next move for a given color, treat the next move as label and
        process the current board situation as feature to learn this label.

        return: X, y - feature and label
        '''
        return NotImplemented

    def process_zip(self, dir_name, zip_file_name, data_file_name, game_list):
        # Read zipped file and extract name list
        this_gz = gzip.open(dir_name + '/' + zip_file_name)
        this_tar_file = zip_file_name[0:-3]
        this_tar = open(dir_name + '/' + this_tar_file, 'wb')
        shutil.copyfileobj(this_gz, this_tar)  # random access needed to tar
        this_tar.close()
        this_zip = tarfile.open(dir_name + '/' + this_tar_file)
        name_list = this_zip.getnames()

        # Determine number of examples
        total_examples = self.num_total_examples(this_zip, game_list, name_list)

        features = np.zeros((total_examples, self.num_planes, 19, 19))
        labels = np.zeros((total_examples,))

        counter = 0
        for index in game_list:
            name = name_list[index + 1]
            if name.endswith('.sgf'):
                '''
                Load Go board and determine handicap of game, then iterate through all moves,
                store preprocessed move in data_file and apply move to board.
                '''
                sgf_content = this_zip.extractfile(name).read()
                sgf, go_board_no_handy = self.init_go_board(sgf_content)
                go_board, first_move_done = self.get_handicap(go_board_no_handy, sgf)
                for item in sgf.main_sequence_iter():
                    color, move = item.get_move()
                    if color is not None and move is not None:
                        row, col = move
                        if first_move_done:
                            X, y = self.feature_and_label(color, move, go_board, self.num_planes)
                            features[counter] = X
                            labels[counter] = y
                            counter += 1
                        go_board.apply_move(color, (row, col))
                        first_move_done = True
            else:
                raise ValueError(name + ' is not a valid sgf')

        feature_file_base = dir_name + '/' + data_file_name + '_features_%d'
        label_file_base = dir_name + '/' + data_file_name + '_labels_%d'

        # Due to files with large content, split up after chunksize
        chunk = 0
        chunksize = 1024
        while features.shape[0] >= chunksize:
            feature_file = feature_file_base % chunk
            label_file = label_file_base % chunk
            chunk += 1
            cur_features, features = features[:chunksize], features[chunksize:]
            cur_labels, labels = labels[:chunksize], labels[chunksize:]
            np.save(feature_file, cur_features)
            np.save(label_file, cur_labels)

    def consolidate_games(self, name, samples):
        print('>>> Creating consolidated numpy arrays')

        if self.use_generator:
            print('>>> Return generator')
            generator = DataGenerator(self.data_dir, samples)
            return generator

        files_needed = set(file_name for file_name, index in samples)
        print('>>> Total number of files: ' + str(len(files_needed)))

        file_names = []
        for zip_file_name in files_needed:
            file_name = zip_file_name.replace('.tar.gz', '') + name
            file_names.append(file_name)

        feature_list = []
        label_list = []
        print(file_names)
        for file_name in file_names:
            file_prefix = file_name.replace('.tar.gz', '')
            base = self.data_dir + '/' + file_prefix + '_features_*.npy'
            print(base)
            for feature_file in glob.glob(base):
                print(feature_file)
                X = np.load(feature_file)
                y = np.load(feature_file)
                feature_list.append(X)
                label_list.append(y)
        print('>>> Done')

        features = np.concatenate(feature_list, axis=0)
        labels = np.concatenate(label_list, axis=0)

        feature_file = self.data_dir + '/' + str(self.num_planes) + '_plane_features_' + name
        label_file = self.data_dir + '/' + str(self.num_planes) + '_plane_labels_' + name

        np.save(feature_file, features)
        np.save(label_file, labels)

        return features, labels


class GoFileProcessor(GoBaseProcessor):
    '''
    GoFileProcessor generates files, e.g. binary representations, of features and labels.
    '''
    def __init__(self, data_directory='data', num_planes=7, consolidate=True):
        super(GoFileProcessor, self).__init__(data_directory=data_directory,
                                              num_planes=num_planes, consolidate=consolidate)

    def store_results(self, data_file, color, move, go_board):
        '''
        Apply current move of given color to provided board and store to data_file.
        '''
        return NotImplemented

    def write_file_header(self, data_file, n, num_planes, board_size, bits_per_pixel):
        headerLine = 'mlv2'
        headerLine = headerLine + '-n=' + str(n)
        headerLine = headerLine + '-num_planes=' + str(num_planes)
        headerLine = headerLine + '-imagewidth=' + str(board_size)
        headerLine = headerLine + '-imageheight=' + str(board_size)
        headerLine = headerLine + '-datatype=int'
        headerLine = headerLine + '-bpp=' + str(bits_per_pixel)
        print(headerLine)
        headerLine = headerLine + "\0\n"
        headerLine = headerLine + chr(0) * (1024 - len(headerLine))
        data_file.write(headerLine)

    def process_zip(self, dir_name, zip_file_name, data_file_name, game_list):
        # Read zipped file and extract name list
        this_gz = gzip.open(dir_name + '/' + zip_file_name)
        this_tar_file = zip_file_name[0:-3]
        this_tar = open(dir_name + '/' + this_tar_file, 'wb')
        shutil.copyfileobj(this_gz, this_tar)  # random access needed to tar
        this_tar.close()
        this_zip = tarfile.open(dir_name + '/' + this_tar_file)
        name_list = this_zip.getnames()

        # Determine number of examples
        total_examples = self.num_total_examples(this_zip, game_list, name_list)
        print('>>> Total number of Go games in this zip: ' + str(total_examples))

        # Write file header
        data_file = open(dir_name + '/' + data_file_name, 'wb')
        self.write_file_header(data_file=data_file, n=total_examples, num_planes=7, board_size=19, bits_per_pixel=1)

        # Write body and close file
        for index in game_list:
            name = name_list[index + 1]
            if name.endswith('.sgf'):
                '''
                Load Go board and determine handicap of game, then iterate through all moves,
                store preprocessed move in data_file and apply move to board.
                '''
                sgf_content = this_zip.extractfile(name).read()
                sgf, go_board_no_handy = self.init_go_board(sgf_content)
                go_board, first_move_done = self.get_handicap(go_board_no_handy, sgf)
                move_idx = 0
                for item in sgf.main_sequence_iter():
                    (color, move) = item.get_move()
                    if color is not None and move is not None:
                        row, col = move
                        if first_move_done:
                            self.store_results(data_file, color, move, go_board)
                        go_board.apply_move(color, (row, col))
                        move_idx = move_idx + 1
                        first_move_done = True
            else:
                raise ValueError(name + ' is not a valid sgf')
        data_file.write('END')
        data_file.close()

    def consolidate_games(self, name, samples):
        print('>>> Creating consolidated .dat...')
        file_path = self.data_dir + '/kgsgo_' + name
        if os.path.isfile(file_path):
            print('>>> File ' + file_path + ' already exists')
            return

        files_needed = set(file_name for file_name, index in samples)
        print('>>> Total dat files to be consolidated: ' + str(len(files_needed)))

        # Collect names of data files
        data_file_names = []
        for zip_file_name in files_needed:
            data_file_name = zip_file_name.replace('.tar.gz', '') + name
            data_file_names.append(data_file_name)

        # Count total number of moves
        num_records = 0
        for data_file_name in data_file_names:
            if not os.path.isfile(self.data_dir + '/' + data_file_name):
                print('>>> Missing file: ' + data_file_name)
                sys.exit(-1)
            child = open(self.data_dir + '/' + data_file_name, 'rb')
            header = child.read(1024)
            this_n = int(header.split('-n=')[1].split('-')[0])
            child.close()
            num_records = num_records + this_n

        # Write content to consolidate file
        consolidated_file = open(file_path, 'wb')
        self.write_file_header(consolidated_file, num_records, self.num_planes, 19, 1)
        for filename in data_file_names:
            print('>>> Reading from ' + filename + ' ...')
            file_path = self.data_dir + '/' + filename
            single_dat = open(file_path, 'rb')
            single_dat.read(1024)
            data = single_dat.read()
            if data[-3:] != 'END':
                raise Exception('Invalid file, doesnt end with END: ' + file_path)
            consolidated_file.write(data[:-3])
            single_dat.close()
        consolidated_file.write('END')
        consolidated_file.close()
