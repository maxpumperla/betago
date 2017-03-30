from __future__ import print_function
import yaml

from keras.models import model_from_yaml
from betago.model import KerasBot
from betago.gtp import GTPFrontend
from betago.processor import SevenPlaneProcessor

processor = SevenPlaneProcessor()

bot_name = 'demo'
model_file = 'model_zoo/' + bot_name + '_bot.yml'
weight_file = 'model_zoo/' + bot_name + '_weights.hd5'


with open(model_file, 'r') as f:
    yml = yaml.load(f)
    model = model_from_yaml(yaml.dump(yml))
    # Note that in Keras 1.0 we have to recompile the model explicitly
    model.compile(loss='categorical_crossentropy', optimizer='adadelta', metrics=['accuracy'])
    model.load_weights(weight_file)

# Start GTP frontend and run model.
frontend = GTPFrontend(bot=KerasBot(model=model, processor=processor))
frontend.run()
