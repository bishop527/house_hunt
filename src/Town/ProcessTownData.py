'''
Created on Nov 10, 2015

@author: ad23883
@todo: 
'''
from utils import *
from Town.ParseTownData import parseTownAdminData
from Town.TownData import getMAZips
from Town.HouseData import getTruliaZipCodeStats
from collections import OrderedDict

def processTownData():
    print ("    Started Processing Town Data")
    
    dataLocation = 'data/town/'
    fileName = 'Master-Town_Data-2015'
    ext = '.xlsx'
    entries = OrderedDict()
      
    entries['Town-Admin'] = parseTownAdminData()
    
    zipCodes = getMAZips()
    entries['Housing-Data'] = getTruliaZipCodeStats(zips=zipCodes, startDate='2015-11-03', endDate='2015-11-04' )
    populateMaster(dataLocation+fileName+ext, entries)
    
    print ("    Done Processing Town Data\n")
    
    # This function doesn't work for most cities, so don't see a use for it yet
    #data = getTruliaNeighborhoods(state='MA', city='Somerset')
    
    # Trulia's list of Zip Codes includes Villages, which does not match up with "official state info
    # such as tax rates. So not able to use.  
    # Use existing town_zips.xlsx instead which has all entries adjusted for municipalities
    #zipCodes = getTruliaZipCodesInState()