from __future__ import print_function
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Conv2D, MaxPooling2D
from keras.utils import np_utils

from betago.processor import SevenPlaneProcessor

batch_size = 128
nb_epoch = 100

nb_classes = 19 * 19  # One class for each position on the board
go_board_rows, go_board_cols = 19, 19  # input dimensions of go board
nb_filters = 32  # number of convolutional filters to use
nb_pool = 2  # size of pooling area for max pooling
nb_conv = 3  # convolution kernel size

# SevenPlaneProcessor loads seven planes (doh!) of 19*19 data points, so we need 7 input channels
processor = SevenPlaneProcessor()
input_channels = processor.num_planes

# Load go data and one-hot encode labels
X, y = processor.load_go_data(num_samples=1000)
X = X.astype('float32')
Y = np_utils.to_categorical(y, nb_classes)

# Specify a keras model with two convolutional layers and two dense layers,
# connecting the (num_samples, 7, 19, 19) input to the 19*19 output vector.
model = Sequential()
model.add(Conv2D(nb_filters, (nb_conv, nb_conv), padding='valid',
                 input_shape=(input_channels, go_board_rows, go_board_cols),
                 data_format='channels_first'))
model.add(Activation('relu'))
model.add(Conv2D(nb_filters, (nb_conv, nb_conv), data_format='channels_first'))
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

model.fit(X, Y, batch_size=batch_size, epochs=nb_epoch, verbose=1)

weight_file = '../model_zoo/weights.hd5'
model.save_weights(weight_file, overwrite=True)

model_file = '../model_zoo/model.yml'
with open(model_file, 'w') as yml:
    model_yaml = model.to_yaml()
    yml.write(model_yaml)
