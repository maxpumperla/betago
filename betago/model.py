from multiprocessing import Process
from flask import Flask, request, jsonify
from flask.ext.cors import CORS
import numpy as np
from .dataloader.goboard import GoBoard
from .processor import ThreePlaneProcessor


class GoModel(object):
    '''
    GoModel is a simple Flask app served on localhost:5000, exposing a REST API to predict
    go moves.
    '''

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

    def predict(self):
        ''' Predict the next move '''
        return NotImplemented

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
            '''
            Predict next move and send to client. Just a wrapper around the abstract predict method.
            '''
            val = self.predict()
            return val

        self.app.run(host='0.0.0.0', debug=True, threaded=True, use_reloader=False)


class KerasBot(GoModel):
    '''
    KerasBot takes top_n predictions of a keras model and tries to apply the best move. If that move is illegal,
    choose the next best, until the list is exhausted. If no more moves are left to play, continue with random
    moves until a legal move is found.
    '''

    def __init__(self, model, processor, top_n=10):
        super(KerasBot, self).__init__(model=model, processor=processor)
        self.top_n = top_n

    def predict(self):
        content = request.json

        # Apply human move
        row = content['i']
        col = content['j']
        color = 'w'
        move = (row, col)
        self.go_board.apply_move(color, move)

        # Preprocess move, make prediction
        X, label = self.processor.feature_and_label(color, move, self.go_board, self.num_planes)
        X = X.reshape((1, X.shape[0], X.shape[1], X.shape[2]))

        # Apply bot move
        bot_color = 'b'
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
                if not self.go_board.is_move_on_board(pred_move):
                    found_move = True
                    self.go_board.apply_move(bot_color, pred_move)
        if not found_move:
            while not found_move:
                pred_row = np.random.randint(19)
                pred_col = np.random.randint(19)
                pred_move = (pred_row, pred_col)
                if not self.go_board.is_move_on_board(pred_move):
                    found_move = True
                    self.go_board.apply_move(bot_color, pred_move)

        # Send back result
        print('Prediction:')
        print(pred_row, pred_col)
        result = {'i': pred_row, 'j': pred_col}
        json_result = jsonify(**result)
        return json_result


class IdiotBot(GoModel):
    '''
    Play random moves, like a good 30k bot.
    '''
    def __init__(self, model=None, processor=ThreePlaneProcessor()):
        super(IdiotBot, self).__init__(model=model, processor=processor)

    def predict(self):
        content = request.json

        self.go_board.apply_move('w', (content['i'], content['j']))

        # Apply bot move
        found_move = False
        if not found_move:
            while not found_move:
                pred_row = np.random.randint(19)
                pred_col = np.random.randint(19)
                pred_move = (pred_row, pred_col)
                if not self.go_board.is_move_on_board(pred_move):
                    found_move = True
                    self.go_board.apply_move('b', pred_move)

        # Send back result
        result = {'i': pred_row, 'j': pred_col}
        json_result = jsonify(**result)
        return json_result
