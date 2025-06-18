'''
Created on 18 June 2025

@author: AD23883
@todo:

'''
import os

MAX_SCORE = 10
MIN_SCORE = -10
MEDIAN_SCORE = 0

# Extension used when saving Excel files
EXT = '.xlsx'

# seconds from 1 Jan 1970 to 2 May 2016 07:00 EST
DEPARTURE_TIME = 1462186800
TRAFFIC_MODEL = 'best_guess'
DESTINATION = '244 Wood St. Lexington, MA'
AVOID_TOLLS = ''

# Location of different data directories
DATA = os.path.join('..', 'data')
HOUSE_DATA = os.path.join('..', 'data', 'house')
SCHOOL_DATA = os.path.join('..', 'data', 'school')
COMMUTE_DATA = os.path.join('..', 'data', 'commute')
TOWN_DATA = os.path.join('..', 'data', 'town')
