import argparse
import os

import numpy as np

from betago.corpora import build_index, find_sgfs, load_index, store_index
from betago.gosgf import Sgf_game
from betago.dataloader import goboard
from betago.processor import SevenPlaneProcessor
from betago.training import TrainingRun

from keras.callbacks import ModelCheckpoint
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.utils import np_utils


def index(args):
    corpus_index = build_index(args.data, args.chunk_size)
    store_index(corpus_index, open(args.output, 'w'))


def show(args):
    corpus_index = load_index(open(args.file))
    print "Index contains %d chunks in %d physical files" % (
        corpus_index.num_chunks, len(corpus_index.physical_files))
    chunk_iterator = corpus_index.get_chunk(corpus_index.num_chunks / 2)
    board, next_color, next_move = next(chunk_iterator)
    print goboard.to_string(board)


def train(args):
    corpus_index = load_index(open(args.index))
    print "Index contains %d chunks in %d physical files" % (
        corpus_index.num_chunks, len(corpus_index.physical_files))
    if not os.path.exists(args.progress):
        run = TrainingRun.create(args.progress, corpus_index)
    else:
        run = TrainingRun.load(args.progress)

    next_chunk = run.chunks_completed
    chunk = corpus_index.get_chunk(next_chunk)

    processor = SevenPlaneProcessor()
    xs, ys = [], []
    for board, next_color, next_move in chunk:
        if next_move is not None:
            # Can't train on passes atm.
            feature, label = processor.feature_and_label(next_color, next_move, board,
                                                         processor.num_planes)
            xs.append(feature)
            ys.append(label)
    X = np.array(xs)
    # one-hot encode the moves
    nb_classes = 19 * 19
    Y = np.zeros((len(ys), nb_classes))
    for i, y in enumerate(ys):
        Y[i][y] = 1

    print "Training epoch %d chunk %d/%d..." % (
        run.epochs_completed + 1,
        run.chunks_completed + 1,
        run.num_chunks)
    run.model.fit(X, Y, nb_epoch=1)

    run.complete_chunk()


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    index_parser = subparsers.add_parser('index', help='Build an index for a corpus.')
    index_parser.set_defaults(command='index')
    index_parser.add_argument('--output', '-o', required=True,
                              help='Path to store the index.')
    index_parser.add_argument('--data', '-d', required=True,
                              help='Directory or archive containing SGF files.')
    index_parser.add_argument('--chunk-size', '-c', type=int, default=20000,
                              help='Number of examples per training chunk.')

    show_parser = subparsers.add_parser('show', help='Show a summary of an index.')
    show_parser.set_defaults(command='show')
    show_parser.add_argument('--file', '-f', required=True, help='Index file.')

    train_parser = subparsers.add_parser('train', help='Do some training.')
    train_parser.set_defaults(command='train')
    train_parser.add_argument('--index', '-i', required=True, help='Index file.')
    train_parser.add_argument('--progress', '-p', required=True, help='Progress file.')

    args = parser.parse_args()

    if args.command == 'index':
        index(args)
    elif args.command == 'show':
        show(args)
    elif args.command == 'train':
        train(args)

if __name__ == '__main__':
    main()
