'''
Created on Nov 10, 2015

@author: ad23883
@todo: 
'''
from utils import *
from House.ParseHouseData import parseTownAdminData, parseMLSHouseData
from House.HouseData import getMAZips
from collections import OrderedDict
import os

def processHouseData(MLS_DATA_FILE):
    print ("    Started Processing House Data")
    
    fileName = 'Master-House_Data-2015'
    entries = OrderedDict()
      
    entries['Town-Admin'] = parseTownAdminData()
    entries['House-Data'] =  parseMLSHouseData(MLS_DATA_FILE)

    populateMaster(os.path.join(houseDataLocation, fileName+ext), entries)
    
    print ("    Done Processing House Data\n")
    