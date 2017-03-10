import warnings
import copy
import json
import os
import numpy as np

from keras import backend as K
from keras import optimizers
from keras.models import Sequential, model_from_config
from keras.optimizers import optimizer_from_config


# Side-port some keras functions to slightly alter their behavior.

def save_model_to_hdf5_group(model, f):
    def get_json_type(obj):
        # if obj is a serializable Keras class instance
        # e.g. optimizer, layer
        if hasattr(obj, 'get_config'):
            return {'class_name': obj.__class__.__name__,
                    'config': obj.get_config()}

        # if obj is any numpy type
        if type(obj).__module__ == np.__name__:
            return obj.item()

        # misc functions (e.g. loss function)
        if callable(obj):
            return obj.__name__

        # if obj is a python 'type'
        if type(obj).__name__ == type.__name__:
            return obj.__name__

        raise TypeError('Not JSON Serializable:', obj)

    from keras import __version__ as keras_version

    f.attrs['keras_version'] = str(keras_version).encode('utf8')
    f.attrs['model_config'] = json.dumps({
        'class_name': model.__class__.__name__,
        'config': model.get_config()
    }, default=get_json_type).encode('utf8')

    model_weights_group = f.create_group('model_weights')
    model.save_weights_to_hdf5_group(model_weights_group)

    if hasattr(model, 'optimizer'):
        if isinstance(model.optimizer, optimizers.TFOptimizer):
            warnings.warn(
                'TensorFlow optimizers do not '
                'make it possible to access '
                'optimizer attributes or optimizer state '
                'after instantiation. '
                'As a result, we cannot save the optimizer '
                'as part of the model save file.'
                'You will have to compile your model again after loading it. '
                'Prefer using a Keras optimizer instead '
                '(see keras.io/optimizers).')
        else:
            f.attrs['training_config'] = json.dumps({
                'optimizer_config': {
                    'class_name': model.optimizer.__class__.__name__,
                    'config': model.optimizer.get_config()
                },
                'loss': model.loss,
                'metrics': model.metrics,
                'sample_weight_mode': model.sample_weight_mode,
                'loss_weights': model.loss_weights,
            }, default=get_json_type).encode('utf8')

            # save optimizer weights
            symbolic_weights = getattr(model.optimizer, 'weights')
            if symbolic_weights:
                optimizer_weights_group = f.create_group('optimizer_weights')
                weight_values = K.batch_get_value(symbolic_weights)
                weight_names = []
                for i, (w, val) in enumerate(zip(symbolic_weights, weight_values)):
                    if hasattr(w, 'name') and w.name:
                        name = str(w.name)
                    else:
                        name = 'param_' + str(i)
                    weight_names.append(name.encode('utf8'))
                optimizer_weights_group.attrs['weight_names'] = weight_names
                for name, val in zip(weight_names, weight_values):
                    param_dset = optimizer_weights_group.create_dataset(
                        name,
                        val.shape,
                        dtype=val.dtype)
                    if not val.shape:
                        # scalar
                        param_dset[()] = val
                    else:
                        param_dset[:] = val


def load_model_from_hdf5_group(f, custom_objects=None):
    if not custom_objects:
        custom_objects = {}

    def deserialize(obj):
        if isinstance(obj, list):
            deserialized = []
            for value in obj:
                if value in custom_objects:
                    deserialized.append(custom_objects[value])
                else:
                    deserialized.append(value)
            return deserialized
        if isinstance(obj, dict):
            deserialized = {}
            for key, value in obj.items():
                if value in custom_objects:
                    deserialized[key] = custom_objects[value]
                else:
                    deserialized[key] = value
            return deserialized
        if obj in custom_objects:
            return custom_objects[obj]
        return obj

    # instantiate model
    model_config = f.attrs.get('model_config')
    if model_config is None:
        raise ValueError('No model found in config file.')
    model_config = json.loads(model_config.decode('utf-8'))
    model = model_from_config(model_config, custom_objects=custom_objects)

    # set weights
    model.load_weights_from_hdf5_group(f['model_weights'])

    # instantiate optimizer
    training_config = f.attrs.get('training_config')
    if training_config is None:
        warnings.warn('No training configuration found in save file: '
                      'the model was *not* compiled. Compile it manually.')
        return model
    training_config = json.loads(training_config.decode('utf-8'))
    optimizer_config = training_config['optimizer_config']
    optimizer = optimizer_from_config(optimizer_config,
                                      custom_objects=custom_objects)

    # recover loss functions and metrics
    loss = deserialize(training_config['loss'])
    metrics = deserialize(training_config['metrics'])
    sample_weight_mode = training_config['sample_weight_mode']
    loss_weights = training_config['loss_weights']

    # compile model
    model.compile(optimizer=optimizer,
                  loss=loss,
                  metrics=metrics,
                  loss_weights=loss_weights,
                  sample_weight_mode=sample_weight_mode)

    # set optimizer weights
    if 'optimizer_weights' in f:
        # build train function (to get weight updates)
        if isinstance(model, Sequential):
            model.model._make_train_function()
        else:
            model._make_train_function()
        optimizer_weights_group = f['optimizer_weights']
        optimizer_weight_names = [n.decode('utf8') for n in optimizer_weights_group.attrs['weight_names']]
        optimizer_weight_values = [optimizer_weights_group[n] for n in optimizer_weight_names]
        model.optimizer.set_weights(optimizer_weight_values)
    return model
