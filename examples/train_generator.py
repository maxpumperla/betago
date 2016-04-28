from __future__ import print_function

import argparse
import os

from keras.callbacks import ModelCheckpoint
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.utils import np_utils

from betago.processor import SevenPlaneProcessor


parser = argparse.ArgumentParser()
parser.add_argument('--bot-name', default='new_bot')
parser.add_argument('--epochs', type=int, default=5)
parser.add_argument('--sample-size', type=int, default=1000)
args = parser.parse_args()

here = os.path.dirname(os.path.abspath(__file__))
model_zoo = os.path.join(here, '..', 'model_zoo')
weight_file = os.path.join(model_zoo, args.bot_name + '_weights.hd5')
checkpoint_file_pattern = os.path.join(model_zoo, args.bot_name + '_epoch_{epoch}.hd5')
model_file = os.path.join(model_zoo, args.bot_name + '_model.yml')

batch_size = 128

nb_classes = 19 * 19  # One class for each position on the board
go_board_rows, go_board_cols = 19, 19  # input dimensions of go board
nb_filters = 32  # number of convolutional filters to use
nb_pool = 2  # size of pooling area for max pooling
nb_conv = 3  # convolution kernel size

# SevenPlaneProcessor loads seven planes (doh!) of 19*19 data points, so we need 7 input channels
processor = SevenPlaneProcessor(use_generator=True)
input_channels = processor.num_planes

# Load go data and one-hot encode labels
data_generator = processor.load_go_data(num_samples=args.sample_size)
print(data_generator.get_num_samples())

# Specify a keras model with two convolutional layers and two dense layers,
# connecting the (num_samples, 7, 19, 19) input to the 19*19 output vector.
model = Sequential()
model.add(Convolution2D(nb_filters, nb_conv, nb_conv, border_mode='valid',
                        input_shape=(input_channels, go_board_rows, go_board_cols)))
model.add(Activation('relu'))
model.add(Convolution2D(nb_filters, nb_conv, nb_conv))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(nb_pool, nb_pool)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(256))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(nb_classes))
model.add(Activation('softmax'))
model.compile(loss='categorical_crossentropy', optimizer='adadelta', metrics=['accuracy'])

model.fit_generator(data_generator.generate(batch_size=batch_size, nb_classes=nb_classes),
                    samples_per_epoch=data_generator.get_num_samples(), nb_epoch=args.epochs,
                    callbacks=[ModelCheckpoint(checkpoint_file_pattern)])

model.save_weights(weight_file, overwrite=True)
with open(model_file, 'w') as yml:
    model_yaml = model.to_yaml()
    yml.write(model_yaml)
