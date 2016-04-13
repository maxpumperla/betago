from multiprocessing import Process
from flask import Flask, request, jsonify
from flask.ext.cors import CORS, cross_origin
import numpy as np
from .dataloader.goboard import GoBoard


class GoModel(object):

    def __init__(self, model, processor):
        self.model = model
        self.processor = processor
        self.go_board = GoBoard(19)
        self.num_planes = processor.num_planes

        self.start_service()

    def predict(self):
        return NotImplemented

    def start_server(self):
        ''' Start Go model server '''
        self.server = Process(target=self.start_service)
        self.server.start()

    def stop_server(self):
        ''' Terminate Go model server '''
        self.server.terminate()
        self.server.join()

    def start_service(self):
        ''' Run flask app'''
        app = Flask(__name__)
        CORS(app, resources={r"/prediction/*": {"origins": "*"}})
        self.app = app

        @app.route('/')
        def home():
            return 'betago'

        @app.route('/prediction', methods=['GET', 'POST'])
        @cross_origin()
        def next_move():
            ''' predict next move and send to client '''
            val = self.predict()
            print(val)
            return val

        self.app.run(host='0.0.0.0', debug=True, threaded=True, use_reloader=False)


class KerasBot(GoModel):

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
    def __init__(self, model, processor):
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
