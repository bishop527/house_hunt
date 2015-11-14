'''
Created on Nov 10, 2015

@author: ad23883
'''
from utils import *

from Town.TownData import getCommuateData
from Town.ParseTownData import parseCommuteData
from Town.ParseTownData import parseTownAdminData
from Town.HouseData import getTruliaCities, getTruliaNeighborhoods,\
    getTruliaZipCodeStats

from collections import OrderedDict

fileName = "house_hunting-Town_Data-2015.xlsx"
entries = OrderedDict()

setCurrDir()
#setProxy()
# commuteData1, commuteData2, commuteData3, commuteData4 = getCommuateData()
# df1 = parseCommuteData(commuteData1)
# df2 = parseCommuteData(commuteData2)
# df3 = parseCommuteData(commuteData3)
# df4 = parseCommuteData(commuteData4)
# frames = [df1,df2,df3,df4]
# entries['Commute'] = pd.concat(frames, ignore_index=True)
# df1.append(df2, ignore_index=True)
# df1.append(df3, ignore_index=True)
# df1.append(df4, ignore_index=True)
# entries['Commute'] = df1
# populateMaster(fileName, entries)

# entries['Town-Admin'] = parseTownAdminData()
# populateMaster(fileName, entries)

#data = getTruliaNeighborhoods(state='MA', city='Somerset')
data = getTruliaZipCodeStats(zip='02726', startDate='2015-11-01', endDate='2015-11-07' )

print ("Done Processing Town Data")