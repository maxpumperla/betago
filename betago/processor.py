import numpy as np
from .dataloader.base_processor import GoDataProcessor, GoFileProcessor


class SevenPlaneProcessor(GoDataProcessor):
    '''
    Implementation of a Go data processor, using seven planes of 19x19 values to represent the position of
    a go board, as explained below.

    This closely reflects the representation suggested in Clark, Storkey:
    http://arxiv.org/abs/1412.3409
    '''

    def __init__(self, data_directory='data',  num_planes=7, consolidate=True):
        super(SevenPlaneProcessor, self).__init__(data_directory=data_directory,
                                                  num_planes=num_planes, consolidate=consolidate)

    def feature_and_label(self, color, move, go_board, num_planes):
        '''
        Parameters
        ----------
        color: color of the next person to move
        move: move they decided to make
        go_board: represents the state of the board before they moved

        Planes we write:
        0: our stones with 1 liberty
        1: our stones with 2 liberty
        2: our stones with 3 or more liberties
        3: their stones with 1 liberty
        4: their stones with 2 liberty
        5: their stones with 3 or more liberties
        6: simple ko
        '''
        row, col = move
        enemy_color = go_board.other_color(color)
        label = row * 19 + col
        move_array = np.zeros((num_planes, go_board.board_size, go_board.board_size))
        for row in range(0, go_board.board_size):
            for col in range(0, go_board.board_size):
                pos = (row, col)
                if go_board.board.get(pos) == color:
                    if go_board.go_strings[pos].liberties.size() == 1:
                        move_array[0, row, col] = 1
                    elif go_board.go_strings[pos].liberties.size() == 2:
                        move_array[1, row, col] = 1
                    elif go_board.go_strings[pos].liberties.size() >= 3:
                        move_array[2, row, col] = 1
                if go_board.board.get(pos) == enemy_color:
                    if go_board.go_strings[pos].liberties.size() == 1:
                        move_array[3, row, col] = 1
                    elif go_board.go_strings[pos].liberties.size() == 2:
                        move_array[4, row, col] = 1
                    elif go_board.go_strings[pos].liberties.size() >= 3:
                        move_array[5, row, col] = 1
                if go_board.is_simple_ko(color, pos):
                    move_array[6, row, col] = 1
        return move_array, label


class ThreePlaneProcessor(GoDataProcessor):
    '''
    Simpler version of the above processor using just three planes. This data processor uses one plane for
    stone positions of each color and one for ko.
    '''

    def __init__(self, data_directory='data', num_planes=3, consolidate=True):
        super(ThreePlaneProcessor, self).__init__(data_directory=data_directory,
                                                  num_planes=num_planes, consolidate=consolidate)

    def feature_and_label(self, color, move, go_board, num_planes):
        '''
        Parameters
        ----------
        color: color of the next person to move
        move: move they decided to make
        go_board: represents the state of the board before they moved

        Planes we write:
        0: our stones
        1: their stones
        2: ko
        '''
        row, col = move
        enemy_color = go_board.other_color(color)
        label = row * 19 + col
        move_array = np.zeros((num_planes, go_board.board_size, go_board.board_size))
        for row in range(0, go_board.board_size):
            for col in range(0, go_board.board_size):
                pos = (row, col)
                if go_board.board.get(pos) == color:
                    move_array[0, row, col] = 1
                if go_board.board.get(pos) == enemy_color:
                    move_array[1, row, col] = 1
                if go_board.is_simple_ko(color, pos):
                    move_array[2, row, col] = 1
        return move_array, label


class SevenPlaneFileProcessor(GoFileProcessor):
    '''
    File processor corresponding to the above data processor. Loading all available data into memory is simply
    not feasible, and this class allows preprocessing into an efficient, binary format.
    '''
    def __init__(self, data_directory='data', num_planes=7, consolidate=True):
        super(SevenPlaneFileProcessor, self).__init__(data_directory=data_directory,
                                                      num_planes=num_planes, consolidate=consolidate)

    def store_results(self, data_file, color, move, go_board):
        '''
        Parameters
        ----------
        color: color of the next person to move
        move: move they decided to make
        go_board: represents the state of the board before they moved

        Planes we write:
        0: our stones with 1 liberty
        1: our stones with 2 liberty
        2: our stones with 3 or more liberties
        3: their stones with 1 liberty
        4: their stones with 2 liberty
        5: their stones with 3 or more liberties
        6: simple ko
        '''
        row, col = move
        enemy_color = go_board.other_color(color)
        data_file.write('GO')
        label = row * 19 + col
        data_file.write(chr(label % 256))
        data_file.write(chr(label // 256))
        data_file.write(chr(0))
        data_file.write(chr(0))
        thisbyte = 0
        thisbitpos = 0
        for plane in range(0, 7):
            for row in range(0, go_board.board_size):
                for col in range(0, go_board.board_size):
                    thisbit = 0
                    pos = (row, col)
                    if go_board.board.get(pos) == color:
                        if plane == 0 and go_board.go_strings[pos].liberties.size() == 1:
                            thisbit = 1
                        elif plane == 1 and go_board.go_strings[pos].liberties.size() == 2:
                            thisbit = 1
                        elif plane == 2 and go_board.go_strings[pos].liberties.size() >= 3:
                            thisbit = 1
                    if go_board.board.get(pos) == enemy_color:
                        if plane == 3 and go_board.go_strings[pos].liberties.size() == 1:
                            thisbit = 1
                        elif plane == 4 and go_board.go_strings[pos].liberties.size() == 2:
                            thisbit = 1
                        elif plane == 5 and go_board.go_strings[pos].liberties.size() >= 3:
                            thisbit = 1
                    if plane == 6 and go_board.is_simple_ko(color, pos):
                            thisbit = 1
                    thisbyte = thisbyte + (thisbit << (7 - thisbitpos))
                    thisbitpos = thisbitpos + 1
                    if thisbitpos == 8:
                        data_file.write(chr(thisbyte))
                        thisbitpos = 0
                        thisbyte = 0
        if thisbitpos != 0:
            data_file.write(chr(thisbyte))
