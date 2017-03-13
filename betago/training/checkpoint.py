import os

import h5py
from keras import backend as K
from keras.models import Sequential, model_from_json
from keras.optimizers import Adadelta
from keras.layers.core import Dense, Dropout, Activation, Flatten
from keras.layers.convolutional import Convolution2D, ZeroPadding2D

from . import kerashack


__all__ = [
    'TrainingRun',
]


class TrainingRun(object):
    def __init__(self, filename, model, epochs_completed, chunks_completed, num_chunks):
        self.filename = filename
        self.model = model
        self.epochs_completed = epochs_completed
        self.chunks_completed = chunks_completed
        self.num_chunks = num_chunks

    def save(self):
        # Backup the original file in case something goes wrong while
        # saving the new checkpoint.
        backup = None
        if os.path.exists(self.filename):
            backup = self.filename + '.bak'
            os.rename(self.filename, backup)

        output = h5py.File(self.filename, 'w')
        model_out = output.create_group('model')
        kerashack.save_model_to_hdf5_group(self.model, model_out)
        metadata = output.create_group('metadata')
        metadata.attrs['epochs_completed'] = self.epochs_completed
        metadata.attrs['chunks_completed'] = self.chunks_completed
        metadata.attrs['num_chunks'] = self.num_chunks
        output.close()

        # If we got here, we no longer need the backup.
        if backup is not None:
            os.unlink(backup)

    def complete_chunk(self):
        self.chunks_completed += 1
        if self.chunks_completed == self.num_chunks:
            self.epochs_completed += 1
            self.chunks_completed = 0
        self.save()

    @classmethod
    def load(cls, filename):
        inp = h5py.File(filename, 'r')
        model = kerashack.load_model_from_hdf5_group(inp['model'])
        training_run = cls(filename,
                           model,
                           inp['metadata'].attrs['epochs_completed'],
                           inp['metadata'].attrs['chunks_completed'],
                           inp['metadata'].attrs['num_chunks'])
        inp.close()
        return training_run

    @classmethod
    def create(cls, filename, index):
        # TODO Take the model architecture as an input.
        model = _big_model()
        opt = Adadelta(clipnorm=0.25)
        model.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy'])
        training_run = cls(filename, model, 0, 0, index.num_chunks)
        training_run.save()
        return training_run



def _big_model():
    model = Sequential()
    model.add(ZeroPadding2D((3, 3), input_shape=(7, 19, 19)))
    model.add(Convolution2D(64, 7, 7, border_mode='valid'))
    model.add(Activation('relu'))

    model.add(ZeroPadding2D((2, 2)))
    model.add(Convolution2D(64, 5, 5))
    model.add(Activation('relu'))

    model.add(ZeroPadding2D((2, 2)))
    model.add(Convolution2D(64, 5, 5))
    model.add(Activation('relu'))

    model.add(ZeroPadding2D((2, 2)))
    model.add(Convolution2D(48, 5, 5))
    model.add(Activation('relu'))

    model.add(ZeroPadding2D((2, 2)))
    model.add(Convolution2D(48, 5, 5))
    model.add(Activation('relu'))

    model.add(ZeroPadding2D((2, 2)))
    model.add(Convolution2D(32, 5, 5))
    model.add(Activation('relu'))

    model.add(ZeroPadding2D((2, 2)))
    model.add(Convolution2D(32, 5, 5))
    model.add(Activation('relu'))

    model.add(Flatten())
    model.add(Dense(1024))
    model.add(Activation('relu'))
    model.add(Dense(19 * 19))
    model.add(Activation('softmax'))
    return model


def _small_model():
    model = Sequential()
    model.add(ZeroPadding2D((3, 3), input_shape=(7, 19, 19)))
    model.add(Convolution2D(48, 7, 7, border_mode='valid'))
    model.add(Activation('relu'))

    model.add(ZeroPadding2D((2, 2)))
    model.add(Convolution2D(32, 5, 5))
    model.add(Activation('relu'))

    model.add(ZeroPadding2D((2, 2)))
    model.add(Convolution2D(32, 5, 5))
    model.add(Activation('relu'))

    model.add(ZeroPadding2D((2, 2)))
    model.add(Convolution2D(32, 5, 5))
    model.add(Activation('relu'))

    model.add(Flatten())
    model.add(Dense(512))
    model.add(Activation('relu'))
    model.add(Dense(19 * 19))
    model.add(Activation('softmax'))
    return model
