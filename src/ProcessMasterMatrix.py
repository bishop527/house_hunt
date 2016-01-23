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

fileName = "Master_Scores-2015.xlsx"

print 'Started Processing Master Matrix'
setCurrDir()
setProxy()

# Gather and parse all the data
# processSchoolData()
processHouseData()
# processCommuteData()
            
# Calculate scores based on the data
scoreEntries = OrderedDict()
scoreEntries['Housing-Scores'] = calculateHouseScores()
scoreEntries['Commute-Scores'] = calculateCommuteScores()
scoreEntries['School-Scores'] = calculateSchoolScores()
populateMaster(fileName, scoreEntries)
scoreEntries['Combined-Scores'] = calculateCombinedScores()
populateMaster(fileName, scoreEntries)

print 'Done Processing Master Matrix'