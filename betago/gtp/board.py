__all__ = [
    'coords_to_gtp_position',
    'gtp_position_to_coords',
]

# 'I' is intentionally omitted.
COLS = 'ABCDEFGHJKLMNOPQRST'


def coords_to_gtp_position(coords):
    """Convert (row, col) tuple to GTP board locations.

    Example:
    >>> coords_to_gtp_position((0, 0))
    'A1'
    """
    row, col = coords
    # coords are zero-indexed, GTP is 1-indexed.
    return COLS[col] + str(row + 1)


def gtp_position_to_coords(gtp_position):
    """Convert a GTP board location to a (row, col) tuple.

    Example:
    >>> gtp_position_to_coords('A1')
    (0, 0)
    """
    col_str, row_str = gtp_position[0], gtp_position[1:]
    return (int(row_str) - 1, COLS.find(col_str))
