from __future__ import absolute_import
import itertools
from six.moves import range


class Territory(object):
    def __init__(self, territory_map):
        self.num_black_territory = 0
        self.num_white_territory = 0
        self.num_black_stones = 0
        self.num_white_stones = 0
        self.num_dame = 0
        self.dame_points = []
        for point, status in territory_map.items():
            if status == 'b':
                self.num_black_stones += 1
            elif status == 'w':
                self.num_white_stones += 1
            elif status == 'territory_b':
                self.num_black_territory += 1
            elif status == 'territory_w':
                self.num_white_territory += 1
            elif status == 'dame':
                self.num_dame += 1
                self.dame_points.append(point)


def evaluate_territory(board):
    """Map a board into territory and dame.

    Any points that are completely surrounded by a single color are
    counted as territory; it makes no attempt to identify even
    trivially dead groups.
    """
    status = {}
    for r, c in itertools.product(list(range(board.board_size)), list(range(board.board_size))):
        if (r, c) in status:
            # Already visited this as part of a different group.
            continue
        if (r, c) in board.board:
            # It's a stone.
            status[r, c] = board.board[r, c]
        else:
            group, neighbors = _collect_region((r, c), board)
            if len(neighbors) == 1:
                # Completely surrounded by black or white.
                fill_with = 'territory_' + neighbors.pop()
            else:
                # Dame.
                fill_with = 'dame'
            for pos in group:
                status[pos] = fill_with
    return Territory(status)


def _collect_region(start_pos, board, visited=None):
    """Find the contiguous section of a board containing a point. Also
    identify all the boundary points.
    """
    if visited is None:
        visited = {}
    if start_pos in visited:
        return [], set()
    all_points = [start_pos]
    all_borders = set()
    visited[start_pos] = True
    here = board.board.get(start_pos)
    r, c = start_pos
    deltas = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for delta_r, delta_c in deltas:
        next_r, next_c = r + delta_r, c + delta_c
        if next_r < 0 or next_r >= board.board_size:
            continue
        if next_c < 0 or next_c >= board.board_size:
            continue
        neighbor = board.board.get((next_r, next_c))
        if neighbor == here:
            points, borders = _collect_region((next_r, next_c), board, visited)
            all_points += points
            all_borders |= borders
        else:
            all_borders.add(neighbor)
    return all_points, all_borders
