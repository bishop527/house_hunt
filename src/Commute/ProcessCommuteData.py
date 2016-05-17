'''
Created on Nov 16, 2015

@author: ad23883
@todo: 
'''
from Commute.ParseCommuteData import parseCommuteData
from Commute.CommuteData import getCommuteData
from utils import *
from collections import OrderedDict
from House.HouseData import getMATowns

def processCommuteData():
    frames = []
    print '    Started Processing Commute Data'
    
    fileName = "Master-Commute_Data-2015"
    entries = OrderedDict()
    
    towns = getMATowns()
        
    """ Need to seperate list of towns into chunks of 100 """
    while len(towns) > 0:
        origins = ''
        for each in towns[:100]:
            origins += each+', MA|'
        origins = origins[:-1]
        
        commuteData = getCommuteData(origins)
        df = parseCommuteData(commuteData)
        frames.append(df)
        
        towns = towns[100:]
        
    entries['Commute-Data'] = pd.concat(frames, ignore_index=True)
    
    populateMaster(os.path.join(commuteDataLocation, fileName+ext), entries)
    
    print '    Done Processing Commute Data\n'