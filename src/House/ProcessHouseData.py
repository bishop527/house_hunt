'''
Created on Nov 10, 2015

@author: ad23883
@todo: 
'''
from utils import *
from House.ParseHouseData import parseTownAdminData, parseMLSHouseData
from House.HouseData import getMAZips
from collections import OrderedDict

def processHouseData():
    print ("    Started Processing House Data")
    
    dataLocation = 'data/house/'
    fileName = 'Master-House_Data-2015'
    ext = '.xlsx'
    entries = OrderedDict()
      
    entries['Town-Admin'] = parseTownAdminData()
    entries['House-Data'] =  parseMLSHouseData()

    populateMaster(dataLocation+fileName+ext, entries)
    
    print ("    Done Processing House Data\n")
    