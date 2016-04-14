import os
import webbrowser
from betago.model import IdiotBot

# Open web frontend
path = os.getcwd().replace('/examples', '')
webbrowser.open('file://' + path + '/ui/demoBot.html', new=2)

# Create an idiot bot, creating random moves and serve it.
go_bot = IdiotBot()
go_bot.run()
