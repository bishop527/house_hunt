'''
Created on Nov 10, 2015

@author: ad23883
'''
from utils import setCurrDir
from utils import setProxy
from utils import populateMaster

from Town.CommuteData import getCommuateData
from Town.ParseTownData import parseCommuteData
from collections import OrderedDict

fileName = "house_hunting-Town_Data-2015.xlsx"
entries = OrderedDict()

setCurrDir()
setProxy()
commuteData1, commuteData2 = getCommuateData()
df1 = parseCommuteData(commuteData1)
df2 = parseCommuteData(commuteData2)
df1.append(df2)
entries['Commute'] = df1

populateMaster(fileName, entries)

print ("Done Adding Town Data")