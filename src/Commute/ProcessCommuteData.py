'''
Created on Nov 16, 2015

@author: ad23883
@todo: 
'''
from collections import OrderedDict
from utils import *
from constants import *
import pandas as pd
from CommuteData import get_commute_data
from ParseCommuteData import parseCommuteData
from House.HouseData import getMATowns

def processCommuteData():
    frames = []
    print('    Started Processing Commute Data')
    
    fileName = "Master-Commute_Data-2025"
    entries = OrderedDict()
    
    towns = getMATowns()
        
    """ Need to separate list of towns into chunks of 100 """
    while len(towns) > 0:
        origins = ''
        for each in towns[:100]:
            origins += each+', MA|'
        origins = origins[:-1]
        
        commuteData = get_commute_data(origins)
        df = parseCommuteData(commuteData)
        frames.append(df)
        
        towns = towns[100:]
        
    entries['Commute-Data'] = pd.concat(frames, ignore_index=True)
    
    populateMaster(os.path.join(COMMUTE_DATA_DIR, fileName + EXT), entries)
    
    print('    Done Processing Commute Data\n')