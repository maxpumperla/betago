import json

from .archive import SGFLocator, find_sgfs
from ..gosgf import Sgf_game

__all__ = [
    'CorpusIndex',
    'build_index',
    'load_index',
    'store_index',
]


class CorpusIndex(object):
    def __init__(self, physical_files, chunk_size, boundaries):
        self.physical_files = list(sorted(physical_files))
        self.chunk_size = chunk_size
        self.boundaries = list(boundaries)

    @property
    def num_chunks(self):
        return len(self.boundaries)

    def serialize(self):
        return {
            'physical_files': self.physical_files,
            'chunk_size': self.chunk_size,
            'boundaries': [boundary.serialize() for boundary in self.boundaries],
        }

    @classmethod
    def deserialize(cls, serialized):
        return cls(
            serialized['physical_files'],
            serialized['chunk_size'],
            [Pointer.deserialize(raw_boundary) for raw_boundary in serialized['boundaries']])


class Pointer(object):
    """Identifies a specific training example inside a corpus."""
    def __init__(self, locator, position):
        self.locator = locator
        self.position = position

    def __str__(self):
        return '%s:%d' % (self.locator, self.position)

    def serialize(self):
        return {
            'locator': self.locator.serialize(),
            'position': self.position,
        }

    @classmethod
    def deserialize(cls, serialized):
        return cls(
            SGFLocator.deserialize(serialized['locator']),
            serialized['position']
        )


def build_index(path, chunk_size):
    """Index all SGF files found in the given location.

    This will include SGF that are contained inside zip or tar archives.
    """
    physical_files = set()
    boundaries = []
    examples_needed = 0
    for sgf in find_sgfs(path):
        physical_files.add(sgf.locator.physical_file)
        if examples_needed == 0:
            # The start of this SGF is a chunk boundary.
            boundaries.append(Pointer(sgf.locator, 0))
            examples_needed = chunk_size
        game_record = Sgf_game.from_string(sgf.contents)
        num_positions = len(game_record.get_main_sequence())
        if examples_needed < num_positions:
            # The start of the next chunk is inside this SGF.
            boundaries.append(Pointer(sgf.locator, examples_needed))
            remaining_examples = num_positions - examples_needed
            examples_needed = chunk_size - remaining_examples
        else:
            # This SGF is entirely contained within the current chunk.
            examples_needed -= num_positions

    return CorpusIndex(physical_files, chunk_size, boundaries)


def load_index(input_stream):
    return CorpusIndex.deserialize(json.load(input_stream))


def store_index(index, output_stream):
    json.dump(index.serialize(), output_stream)
