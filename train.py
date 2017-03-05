import argparse

from betago.corpora import build_index, find_sgfs, load_index, store_index
from betago.gosgf import Sgf_game
from betago.dataloader import goboard


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

    args = parser.parse_args()

    if args.command == 'index':
        index(args)
    elif args.command == 'show':
        show(args)

if __name__ == '__main__':
    main()
