'''
Created on Nov 16, 2015

@author: ad23883
@todo: 
'''

from utils import *
import os
from collections import OrderedDict
from Commute.ProcessCommuteData import processCommuteData
from Commute.CommuteScore import calculateCommuteScores
from School.ProcessSchoolData import processSchoolData
from School.SchoolScore import calculateSchoolScores
from House.ProcessHouseData import processHouseData
from House.HousingScore import calculateHouseScores
from CombinedScores import calculateCombinedScores

#masterFile = os.path.join(dataLocation, MASTER_FILE_NAME)
traffic = 'bg'
mls = 'Aug-2015'

print 'Choose an MLS data file'
print '  1 = August 2015'
print '  2 = October 2015'
uMLSData = int(raw_input('mls data: '))
if uMLSData == 1: 
    MLS_DATA_FILE = 'mls_house_data-Aug_2015'
    mls = 'Aug-2015'
elif uMLSData == 2: 
    MLS_DATA_FILE = 'mls_house_data-Oct_2015'
    mls = 'Oct-2015'

if raw_input('Set traffic model? [y/n]') == 'y':
    print '  1 = best_guess'
    print '  2 = optimistic'
    print '  3 = pessimistic '
    uTrafficModel = int(raw_input('model: '))
    if uTrafficModel == 1: 
        TRAFFIC_MODEL = 'best_guess'
        traffic = 'best'
    elif uTrafficModel == 2: 
        TRAFFIC_MODEL = 'optimistic'
        traffic = 'opt'
    elif uTrafficModel == 3: 
        TRAFFIC_MODEL = 'pessimistic'
        traffic = 'pess'
        
masterFileName = os.path.join(dataLocation, 'Master_Scores-'+mls+'-'+traffic)
    
uProxy = raw_input('Behind a proxy? [y/N]')
uHouseData = raw_input('Do you want to update house data? [Y/n] ')
uCommuteData = raw_input('Do you want to update commute data? [Y/n] ')
uSchoolData = raw_input('Do you want to update school data? [Y/n] ')

print 'Started Processing Master Matrix'

if uSchoolData != 'n':
    processSchoolData()
if uHouseData != 'n':
    processHouseData(MLS_DATA_FILE)
if uCommuteData != 'n':
    processCommuteData()
            
# Calculate scores based on the data
scoreEntries = OrderedDict()
scoreEntries['Housing-Scores'] = calculateHouseScores()
scoreEntries['Commute-Scores'] = calculateCommuteScores()
scoreEntries['School-Scores'] = calculateSchoolScores()
populateMaster(masterFileName+ext, scoreEntries)
scoreEntries['Combined-Scores'] = calculateCombinedScores(masterFileName)
populateMaster(masterFileName+ext, scoreEntries)

print 'Done Processing Master Matrix'