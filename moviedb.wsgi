#!/usr/bin/python3

import sys
import os
sys.path.insert(0, '/var/www/MovieDB')

os.environ['MOVIE_DB_PATH'] = '/home/db/Documents/MovieDBfiles'
os.environ['IMDB_API_KEY'] = 'your_api_key'
os.environ['SCRIPT_NAME'] = '/moviedb'

from moviedb import app as application