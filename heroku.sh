#!/bin/bash
python app.py --port $PORT
python worker.py
