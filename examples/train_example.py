from __future__ import print_function
from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, MaxPooling2D
from keras.utils import np_utils
from keras.models import model_from_yaml
import yaml

from omegago.dataloader.processor import SevenPlaneProcessor

batch_size = 128
nb_classes = 19 * 19
nb_epoch = 1

# input image dimensions
go_board_rows, go_board_cols = 19, 19
# number of convolutional filters to use
nb_filters = 32
# size of pooling area for max pooling
nb_pool = 2
# convolution kernel size
nb_conv = 3

# SevenPlaneProcessor loads seven planes (doh!) of 19*19 data points, so we need 7 input channels
processor = SevenPlaneProcessor()
input_channels = processor.num_planes

X, y = processor.load_go_data(num_samples=1000)

X = X.astype('float32')
print('X shape:', X.shape)
print(X.shape[0], 'train samples')

# convert class vectors to binary class matrices
Y_train = np_utils.to_categorical(y, nb_classes)

model = Sequential()
model.add(Convolution2D(nb_filters, nb_conv, nb_conv, border_mode='valid',
                        input_shape=(input_channels, go_board_rows, go_board_cols)))
model.add(Activation('relu'))
model.add(Convolution2D(nb_filters, nb_conv, nb_conv))
model.add(Activation('relu'))
model.add(MaxPooling2D(pool_size=(nb_pool, nb_pool)))
model.add(Dropout(0.25))
model.add(Flatten())
model.add(Dense(128))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(nb_classes))
model.add(Activation('softmax'))

model.compile(loss='categorical_crossentropy', optimizer='adadelta')

model.fit(X, Y_train, batch_size=batch_size, nb_epoch=nb_epoch,
          show_accuracy=True, verbose=1)

model_file = '../model_zoo/model.yml'
weight_file = '../model_zoo/weights.hd5'

model.save_weights(weight_file, overwrite=True)


with open(model_file, 'w') as yml:
    model_yaml = model.to_yaml()
    yml.write(model_yaml)
    model_from_yaml(model_yaml)

with open(model_file, 'r') as f:
    yml = yaml.load(f)
    yml = yaml.dump(yml)
    print(yml)
    re_model = model_from_yaml(yml)

re_model.load_weights(weight_file)

# TODO: Serialize model and weights, store them in models subfolder
# TODO: Create a go_model flask app from a model and a preprocessor
# TODO: Serve the model and connect to UI
