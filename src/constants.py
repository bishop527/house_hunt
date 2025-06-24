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
# DEPARTURE_TIME = 1462186800
TRAFFIC_MODEL = 'best_guess'
WORK_ADDR = '244 Wood St. Lexington, MA'
AVOID_TOLLS = ''

# Location of different data directories
BASE = os.path.join(os.sep, 'home', 'ad23883', 'workspace', 'house_hunt')
DATA = os.path.join(BASE, 'data')
HOUSE_DATA = os.path.join(BASE, DATA, 'house')
SCHOOL_DATA = os.path.join(BASE, DATA, 'school')
COMMUTE_DATA = os.path.join(BASE, DATA, 'commute')
TOWN_DATA = os.path.join(BASE, DATA, 'town')

KEY_LOC = DATA
KEY_FILE = "key"