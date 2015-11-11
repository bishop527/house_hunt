'''
Created on Nov 10, 2015

@author: ad23883
'''
from utils import *
from Town.CommuteData import getCommuateData
from Town.ParseTownData import parseCommuteData
from collections import OrderedDict

fileName = "house_hunting-Town_Data-2015.xlsx"
entries = OrderedDict()

setCurrDir()
#utils.setProxy()
commuteData = getCommuateData()
entries['Commute'] = parseCommuteData(commuteData)

populateMaster(fileName, entries)

print ("Done Adding Town Data")