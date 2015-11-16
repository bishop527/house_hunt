'''
Created on Nov 16, 2015

@author: ad23883
@todo: 
'''

from utils import *
from Commute.ProcessCommuteData import processCommuteData
from School.ProcessSchoolData import processSchoolData
from Town.ProcessTownData import processTownData

fileName = "Master-House_Hunt_Matrix-2015.xlsx"

print 'Started Processing Master Matrix'
setCurrDir()
setProxy()

processSchoolData()
processTownData()
processCommuteData()

print 'Done Processing Master Matrix'