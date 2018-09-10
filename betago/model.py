from __future__ import absolute_import
from __future__ import print_function
import copy
import random
from itertools import chain, product
from multiprocessing import Process

from flask import Flask, request, jsonify
from flask_cors import CORS
import numpy as np
from . import scoring
from .dataloader.goboard import GoBoard
from .processor import ThreePlaneProcessor
from six.moves import range


class HTTPFrontend(object):
    '''
    HTTPFrontend is a simple Flask app served on localhost:8080, exposing a REST API to predict
    go moves.
    '''

    def __init__(self, bot, graph, port=8080):
        self.bot = bot
        self.graph = graph
        self.port = port

    def start_server(self):
        ''' Start Go model server '''
        self.server = Process(target=self.start_service)
        self.server.start()

    def stop_server(self):
        ''' Terminate Go model server '''
        self.server.terminate()
        self.server.join()

    def run(self):
        ''' Run flask app'''
        app = Flask(__name__)
        CORS(app, resources={r"/prediction/*": {"origins": "*"}})
        self.app = app

        @app.route('/dist/<path:path>')
        def static_file_dist(path):
            return open("ui/dist/" + path).read()

        @app.route('/large/<path:path>')
        def static_file_large(path):
            return open("ui/large/" + path).read()

        @app.route('/')
        def home():
            # Inject game data into HTML
            board_init = 'initialBoard = ""' # backup variable
            board = {}
            for row in range(19):
                board_row = {}
                for col in range(19):
                    # Get the cell value
                    cell = str(self.bot.go_board.board.get((col, row)))
                    # Replace values with numbers
                    # Value will be be 'w' 'b' or None
                    cell = cell.replace("None", "0")
                    cell = cell.replace("b", "1")
                    cell = cell.replace("w", "2")
                    # Add cell to row
                    board_row[col] = int(cell) # must be an int
                # Add row to board
                board[row] = board_row
            board_init = str(board) # lazy convert list to JSON
            
            return open("ui/demoBot.html").read().replace('"__i__"', 'var boardInit = ' + board_init) # output the modified HTML file

        @app.route('/sync', methods=['GET', 'POST'])
        def exportJSON():
            export = {}
            export["hello"] = "yes?"
            return jsonify(**export)

        @app.route('/prediction', methods=['GET', 'POST'])
        def next_move():
            '''Predict next move and send to client.

            Parses the move and hands the work off to the bot.
            '''
            with self.graph.as_default():
                content = request.json
                col = content['i']
                row = content['j']
                print('Received move:')
                print((col, row))
                self.bot.apply_move('b', (row, col))

                bot_row, bot_col = self.bot.select_move('w')
                print('Prediction:')
                print((bot_col, bot_row))
                result = {'i': bot_col, 'j': bot_row}
                json_result = jsonify(**result)
                return json_result

        self.app.run(host='0.0.0.0', port=self.port, debug=True, use_reloader=False)


class GoModel(object):
    '''Tracks a board and selects moves.'''

    def __init__(self, model, processor):
        '''
        Parameters:
        -----------
        processor: Instance of betago.processor.GoDataLoader, e.g. SevenPlaneProcessor
        model: In principle this can be anything that can predict go moves, given data provided by the above
               processor. In practice it may very well be (an extension of) a keras model plus glue code.
        '''
        self.model = model
        self.processor = processor
        self.go_board = GoBoard(19)
        self.num_planes = processor.num_planes

    def set_board(self, board):
        '''Set the board to a specific state.'''
        self.go_board = copy.deepcopy(board)

    def apply_move(self, color, move):
        ''' Apply the human move'''
        return NotImplemented

    def select_move(self, bot_color):
        ''' Select a move for the bot'''
        return NotImplemented


class KerasBot(GoModel):
    '''
    KerasBot takes top_n predictions of a keras model and tries to apply the best move. If that move is illegal,
    choose the next best, until the list is exhausted. If no more moves are left to play, continue with random
    moves until a legal move is found.
    '''

    def __init__(self, model, processor, top_n=10):
        super(KerasBot, self).__init__(model=model, processor=processor)
        self.top_n = top_n

    def apply_move(self, color, move):
        # Apply human move
        self.go_board.apply_move(color, move)

    def select_move(self, bot_color):
        move = get_first_valid_move(self.go_board, bot_color,
                                    self._move_generator(bot_color))
        if move is not None:
            self.go_board.apply_move(bot_color, move)
        return move

    def _move_generator(self, bot_color):
        return chain(
            # First try the model.
            self._model_moves(bot_color),
            # If none of the model moves are valid, fill in a random
            # dame point. This is probably not a very good move, but
            # it's better than randomly filling in our own eyes.
            fill_dame(self.go_board),
            # Lastly just try any open space.
            generate_in_random_order(all_empty_points(self.go_board)),
        )

    def _model_moves(self, bot_color):
        # Turn the board into a feature vector.
        # The (0, 0) is for generating the label, which we ignore.
        X, label = self.processor.feature_and_label(
            bot_color, (0, 0), self.go_board, self.num_planes)
        X = X.reshape((1, X.shape[0], X.shape[1], X.shape[2]))

        # Generate bot move.
        pred = np.squeeze(self.model.predict(X))
        top_n_pred_idx = pred.argsort()[-self.top_n:][::-1]
        for idx in top_n_pred_idx:
            prediction = int(idx)
            pred_row = prediction // 19
            pred_col = prediction % 19
            pred_move = (pred_row, pred_col)
            yield pred_move


class RandomizedKerasBot(GoModel):
    '''
    Takes a weighted sample from the predictions of a keras model. If none of those moves is legal,
    pick a random move.
    '''

    def __init__(self, model, processor):
        super(RandomizedKerasBot, self).__init__(model=model, processor=processor)

    def apply_move(self, color, move):
        # Apply human move
        self.go_board.apply_move(color, move)

    def select_move(self, bot_color):
        move = get_first_valid_move(self.go_board, bot_color,
                                    self._move_generator(bot_color))
        if move is not None:
            self.go_board.apply_move(bot_color, move)
        return move

    def _move_generator(self, bot_color):
        return chain(
            # First try the model.
            self._model_moves(bot_color),
            # If none of the model moves are valid, fill in a random
            # dame point. This is probably not a very good move, but
            # it's better than randomly filling in our own eyes.
            fill_dame(self.go_board),
            # Lastly just try any open space.
            generate_in_random_order(all_empty_points(self.go_board)),
        )

    def _model_moves(self, bot_color):
        # Turn the board into a feature vector.
        # The (0, 0) is for generating the label, which we ignore.
        X, label = self.processor.feature_and_label(
            bot_color, (0, 0), self.go_board, self.num_planes)
        X = X.reshape((1, X.shape[0], X.shape[1], X.shape[2]))

        # Generate moves from the keras model.
        n_samples = 20
        pred = np.squeeze(self.model.predict(X))
        # Cube the predictions to increase the difference between the
        # best and worst moves. Otherwise, it will make too many
        # nonsense moves. (There's no scientific basis for this, it's
        # just an ad-hoc adjustment)
        pred = pred * pred * pred
        pred /= pred.sum()
        moves = np.random.choice(19 * 19, size=n_samples, replace=False, p=pred)
        for prediction in moves:
            pred_row = prediction // 19
            pred_col = prediction % 19
            yield (pred_row, pred_col)


class IdiotBot(GoModel):
    '''
    Play random moves, like a good 30k bot.
    '''

    def __init__(self, model=None, processor=ThreePlaneProcessor()):
        super(IdiotBot, self).__init__(model=model, processor=processor)

    def apply_move(self, color, move):
        self.go_board.apply_move(color, move)

    def select_move(self, bot_color):
        move = get_first_valid_move(
            self.go_board,
            bot_color,
            # TODO: this function is gone. retrieve it.
            generate_randomized(all_empty_points(self.go_board))
        )

        if move is not None:
            self.go_board.apply_move(bot_color, move)
        return move


def get_first_valid_move(board, color, move_generator):
    for move in move_generator:
        if move is None or board.is_move_legal(color, move):
            return move
    return None


def generate_in_random_order(point_list):
    """Yield all points in the list in a random order."""
    point_list = copy.copy(point_list)
    random.shuffle(point_list)
    for candidate in point_list:
        yield candidate


def all_empty_points(board):
    """Return all empty positions on the board."""
    empty_points = []
    for point in product(list(range(board.board_size)), list(range(board.board_size))):
        if point not in board.board:
            empty_points.append(point)
    return empty_points


def fill_dame(board):
    status = scoring.evaluate_territory(board)
    # Pass when all dame are filled.
    if status.num_dame == 0:
        yield None
    for dame_point in generate_in_random_order(status.dame_points):
        yield dame_point
