import argparse
import yaml

from keras.models import model_from_yaml
from betago import scoring
from betago.dataloader import goboard
from betago.model import KerasBot
from betago.processor import SevenPlaneProcessor
from betago.simulate import simulate_game


def load_keras_bot(bot_name):
    bot_name = 'one_epoch_cnn'
    model_file = 'model_zoo/' + bot_name + '_bot.yml'
    weight_file = 'model_zoo/' + bot_name + '_weights.hd5'
    with open(model_file, 'r') as f:
        yml = yaml.load(f)
        model = model_from_yaml(yaml.dump(yml))
        # Note that in Keras 1.0 we have to recompile the model explicitly
        model.compile(loss='categorical_crossentropy', optimizer='adadelta', metrics=['accuracy'])
        model.load_weights(weight_file)
    processor = SevenPlaneProcessor()
    return KerasBot(model=model, processor=processor)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('black_bot_name')
    parser.add_argument('white_bot_name')
    parser.add_argument('--komi', '-k', type=float, default=5.5)
    args = parser.parse_args()

    black_bot = load_keras_bot(args.black_bot_name)
    white_bot = load_keras_bot(args.white_bot_name)

    print("Simulating %s vs %s..." % (args.black_bot_name, args.white_bot_name))
    board = goboard.GoBoard()
    simulate_game(board, black_bot=black_bot, white_bot=white_bot)
    print("Game over!")
    print(goboard.to_string(board))
    # Does not remove dead stones.
    print("\nScore (Chinese rules):")
    status = scoring.evaluate_territory(board)
    black_area = status.num_black_territory + status.num_black_stones
    white_area = status.num_white_territory + status.num_white_stones
    white_score = white_area + args.komi
    print("Black %d" % black_area)
    print("White %d + %.1f = %.1f" % (white_area, args.komi, white_score))


if __name__ == '__main__':
    main()
