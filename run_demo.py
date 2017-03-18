from __future__ import print_function
import argparse
import yaml
import os
import webbrowser

from keras.models import model_from_yaml
from betago.model import HTTPFrontend, KerasBot
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

parser = argparse.ArgumentParser()
parser.add_argument('--port', '-p', type=int, default=8080,
                    help='Port the web server should listen on (default 8080).')
args = parser.parse_args()

# Open web frontend and serve model
webbrowser.open('http://localhost:%d/' % (args.port,), new=2)
go_model = KerasBot(model=model, processor=processor)
go_server = HTTPFrontend(bot=go_model, port=args.port)
go_server.run()
