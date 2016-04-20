from multiprocessing import Process
from flask import Flask, request, jsonify
from flask.ext.cors import CORS
import numpy as np
from .dataloader.goboard import GoBoard
from .processor import ThreePlaneProcessor


class HTTPFrontend(object):
    '''
    HTTPFrontend is a simple Flask app served on localhost:5000, exposing a REST API to predict
    go moves.
    '''
    def __init__(self, bot):
        self.bot = bot

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

        @app.route('/')
        def home():
            return 'betago'

        @app.route('/prediction', methods=['GET', 'POST'])
        def next_move():
            '''Predict next move and send to client.

            Parses the move and hands the work off to the bot.
            '''
            content = request.json
            row = content['i']
            col = content['j']
            self.bot.apply_move('w', (row, col))

            bot_row, bot_col = self.bot.select_move('b')
            print('Prediction:')
            print(bot_row, bot_col)
            result = {'i': bot_row, 'j': bot_col}
            json_result = jsonify(**result)
            return json_result

        self.app.run(host='0.0.0.0', debug=True, threaded=True, use_reloader=False)


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
        # Turn the board into a feature vector.
        # The (0, 0) is for generating the label, which we ignore.
        X, label = self.processor.feature_and_label(bot_color, (0, 0), self.go_board, self.num_planes)
        X = X.reshape((1, X.shape[0], X.shape[1], X.shape[2]))

        # Generate bot move.
        found_move = False
        top_n = 10

        pred = np.squeeze(self.model.predict(X))
        top_n_pred_idx = pred.argsort()[-top_n:][::-1]
        for idx in top_n_pred_idx:
            if not found_move:
                prediction = int(idx)
                pred_row = prediction // 19
                pred_col = prediction % 19
                pred_move = (pred_row, pred_col)
                if self.go_board.is_move_legal(bot_color, pred_move):
                    found_move = True
                    self.go_board.apply_move(bot_color, pred_move)
        if not found_move:
            while not found_move:
                pred_row = np.random.randint(19)
                pred_col = np.random.randint(19)
                pred_move = (pred_row, pred_col)
                if self.go_board.is_move_legal(bot_color, pred_move):
                    found_move = True
                    self.go_board.apply_move(bot_color, pred_move)

        return pred_move


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
        # Turn the board into a feature vector.
        # The (0, 0) is for generating the label, which we ignore.
        X, label = self.processor.feature_and_label(bot_color, (0, 0), self.go_board, self.num_planes)
        X = X.reshape((1, X.shape[0], X.shape[1], X.shape[2]))

        # Generate bot move.
        found_move = False
        n_samples = 25
        pred = np.squeeze(self.model.predict(X))
        # Square the predictions to increase the difference between the
        # best and worst moves. Otherwise, it will make too many
        # nonsense moves. (There's no scientific basis for this, it's
        # just an ad-hoc adjustment)
        pred *= pred
        pred /= pred.sum()
        moves = np.random.choice(19 * 19, size=n_samples, replace=False, p=pred)
        for prediction in moves:
            pred_row = prediction // 19
            pred_col = prediction % 19
            pred_move = (pred_row, pred_col)
            if self.go_board.is_move_legal(bot_color, pred_move):
                found_move = True
                self.go_board.apply_move(bot_color, pred_move)
                break
        # None of the model's choices were valid; pick a random move.
        if not found_move:
            while not found_move:
                pred_row = np.random.randint(19)
                pred_col = np.random.randint(19)
                pred_move = (pred_row, pred_col)
                if self.go_board.is_move_legal(bot_color, pred_move):
                    found_move = True
                    self.go_board.apply_move(bot_color, pred_move)

        return pred_move


class IdiotBot(GoModel):
    '''
    Play random moves, like a good 30k bot.
    '''
    def __init__(self, model=None, processor=ThreePlaneProcessor()):
        super(IdiotBot, self).__init__(model=model, processor=processor)

    def apply_move(self, color, move):
        self.go_board.apply_move(color, move)

    def select_move(self, bot_color):
        found_move = False
        if not found_move:
            while not found_move:
                pred_row = np.random.randint(19)
                pred_col = np.random.randint(19)
                pred_move = (pred_row, pred_col)
                if self.go_board.is_move_legal(bot_color, pred_move):
                    found_move = True
                    self.go_board.apply_move(bot_color, pred_move)

        return pred_move
