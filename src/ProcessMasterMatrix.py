'''
Created on Nov 16, 2015

@author: ad23883
@todo: 
'''

from utils import *
from collections import OrderedDict
from Commute.ProcessCommuteData import processCommuteData
from Commute.CommuteScore import calculateCommuteScores
from School.ProcessSchoolData import processSchoolData
from School.SchoolScore import calculateSchoolScores
from House.ProcessHouseData import processHouseData
from House.HousingScore import calculateHouseScores
from CombinedScores import calculateCombinedScores

fileName = "Master_Scores-2015"

uProxy = raw_input('Behind a proxy? [y/N]')
uHouseData = raw_input('Do you want to update house data? [Y/n] ')
uCommuteData = raw_input('Do you want to update commute data? [Y/n] ')
uSchoolData = raw_input('Do you want to update school data? [Y/n] ')


print 'Started Processing Master Matrix'
if uProxy == 'y':
    setProxy()

# Gather and parse all the data
if uSchoolData != 'n':
    processSchoolData()
if uHouseData != 'n':
    processHouseData()
if uCommuteData != 'n':
    processCommuteData()
            
# Calculate scores based on the data
scoreEntries = OrderedDict()
scoreEntries['Housing-Scores'] = calculateHouseScores()
scoreEntries['Commute-Scores'] = calculateCommuteScores()
scoreEntries['School-Scores'] = calculateSchoolScores()
populateMaster(fileName+ext, scoreEntries)
scoreEntries['Combined-Scores'] = calculateCombinedScores()
populateMaster(fileName+ext, scoreEntries)

print 'Done Processing Master Matrix'