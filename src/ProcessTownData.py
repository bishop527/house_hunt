'''
Created on Nov 10, 2015

@author: ad23883
'''
from utils import *

from Town.TownData import getCommuateData, getMAZips
from Town.ParseTownData import parseCommuteData
from Town.ParseTownData import parseTownAdminData
from Town.HouseData import getTruliaCities, getTruliaNeighborhoods,\
    getTruliaZipCodeStats, getTruliaZipCodesInState

from collections import OrderedDict

fileName = "house_hunting-Town_Data-2015.xlsx"
entries = OrderedDict()

setCurrDir()
setProxy()
commuteData1, commuteData2, commuteData3, commuteData4 = getCommuateData()
df1 = parseCommuteData(commuteData1)
df2 = parseCommuteData(commuteData2)
df3 = parseCommuteData(commuteData3)
df4 = parseCommuteData(commuteData4)
# frames = [df1,df2,df3,df4]
# entries['Commute'] = pd.concat(frames, ignore_index=True)
df1.append(df2, ignore_index=True)
df1.append(df3, ignore_index=True)
df1.append(df4, ignore_index=True)
entries['Commute'] = df1
populateMaster(fileName, entries)
  
entries['Town-Admin'] = parseTownAdminData()
populateMaster(fileName, entries)

# This function doesn't work for most cities, so don't see a use for it yet
#data = getTruliaNeighborhoods(state='MA', city='Somerset')

# Trulia's list of Zip Codes includes Villages, which does not match up with "official state info
# such as tax rates. So not able to use.  
# Use existing town_zips.xlsx instead which has all entries adjusted for municipalities
#zipCodes = getTruliaZipCodesInState()

zipCodes = getMAZips()
data = getTruliaZipCodeStats(zips=zipCodes, startDate='2015-11-03', endDate='2015-11-04' )

print ("Done Processing Town Data")