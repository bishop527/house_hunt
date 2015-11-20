'''
Created on Nov 16, 2015

@author: ad23883
@todo: 
'''

from utils import *
from Commute.ProcessCommuteData import processCommuteData
from Commute.CommuteScore import calculateCommuteScores
from School.ProcessSchoolData import processSchoolData
from School.SchoolScore import calculateSchoolScores
from Town.ProcessTownData import processTownData
from Town.HousingScore import calculateHousingScores

fileName = "Master-House_Hunt_Matrix-2015.xlsx"

print 'Started Processing Master Matrix'
setCurrDir()
setProxy()

# Gather and parse all the data
processSchoolData()
processTownData()
processCommuteData()
            
# Calculate scores based on the data
calculateHousingScores()
calculateCommuteScores()
calculateSchoolScores()

print 'Done Processing Master Matrix'