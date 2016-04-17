from __future__ import print_function
import yaml
import os
import webbrowser

from keras.models import model_from_yaml
from betago.model import KerasBot
from betago.processor import SevenPlaneProcessor

processor = SevenPlaneProcessor()

bot_name = '100_epochs_cnn'
model_file = 'model_zoo/' + bot_name + '_bot.yml'
weight_file = 'model_zoo/' + bot_name + '_weights.hd5'


with open(model_file, 'r') as f:
    yml = yaml.load(f)
    model = model_from_yaml(yaml.dump(yml))
    # Note that in Keras 1.0 we have to recompile the model explicitly
    model.compile(loss='categorical_crossentropy', optimizer='adadelta', metrics=['accuracy'])
    model.load_weights(weight_file)

# Open web frontend and serve model
webbrowser.open('file://' + os.getcwd() + '/ui/demoBot.html', new=2)
go_model = KerasBot(model=model, processor=processor)
go_model.run()
