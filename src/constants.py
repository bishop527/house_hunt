'''
Created on 18 June 2025

@author: AD23883
@todo:

'''
import os
import datetime

MAX_SCORE = 10
MIN_SCORE = -10
MEDIAN_SCORE = 0

# Extension used when saving Excel files
EXT = '.xlsx'

# seconds from 1 Jan 1970 to 2 May 2016 07:00 EST
EPOCH = datetime.datetime(1970,1,1,0,0,0)
DEPARTURE_TIME = 1462186800
TRAFFIC_MODEL = 'best_guess'
WORK_ADDR = '244 Wood St. Lexington, MA'
AVOID_TOLLS = ''

# Location of different data directories
BASE_DIR = os.path.join(os.sep, "Users", "aedwa", "workspace", "house_hunt")
# BASE_DIR = os.path.join(os.sep, 'home', 'ad23883', 'workspace', 'house_hunt')
DATA_DIR = os.path.join(BASE_DIR, 'data')
HOUSE_DATA = os.path.join(BASE_DIR, DATA_DIR, 'house')
SCHOOL_DATA = os.path.join(BASE_DIR, DATA_DIR, 'school')
COMMUTE_DATA_DIR = os.path.join(BASE_DIR, DATA_DIR, 'commute')
TOWN_DATA = os.path.join(BASE_DIR, DATA_DIR, 'town')
API_KEY_FILE = os.path.join(BASE_DIR, DATA_DIR, 'googleapi')

KEY_LOC = DATA_DIR
KEY_FILE = "key"