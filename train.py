import argparse

import numpy as np

from betago.corpora import build_index, find_sgfs, load_index, store_index
from betago.gosgf import Sgf_game
from betago.dataloader import goboard
from betago.processor import SevenPlaneProcessor

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
    corpus_index = load_index(open(args.file))
    print "Index contains %d chunks in %d physical files" % (
        corpus_index.num_chunks, len(corpus_index.physical_files))
    chunk_iterator = corpus_index.get_chunk(args.chunk)
    processor = SevenPlaneProcessor()
    xs, ys = [], []
    for i, (board, next_color, next_move) in enumerate(chunk_iterator):
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


    print "Compile model..."
    nb_filters = 30
    nb_conv = 5
    input_channels = 7
    model = Sequential()
    model.add(Convolution2D(nb_filters, nb_conv, nb_conv, border_mode='valid',
                            input_shape=(input_channels, 19, 19)))
    model.add(Activation('relu'))
    model.add(Convolution2D(nb_filters, nb_conv, nb_conv))
    model.add(Activation('relu'))
    model.add(Dropout(0.25))
    model.add(Flatten())
    model.add(Dense(256))
    model.add(Activation('relu'))
    model.add(Dropout(0.5))
    model.add(Dense(nb_classes))
    model.add(Activation('softmax'))
    model.compile(loss='categorical_crossentropy', optimizer='adadelta', metrics=['accuracy'])

    print "Train model..."
    model.fit(X, Y, nb_epoch=1)


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

    train_parser = subparsers.add_parser('train', help='Train on a chunk.')
    train_parser.set_defaults(command='train')
    train_parser.add_argument('--file', '-f', required=True, help='Index file.')
    train_parser.add_argument('--chunk', '-c', type=int, default=0,
                              help='Chunk number to train on.')

    args = parser.parse_args()

    if args.command == 'index':
        index(args)
    elif args.command == 'show':
        show(args)
    elif args.command == 'train':
        train(args)

if __name__ == '__main__':
    main()
