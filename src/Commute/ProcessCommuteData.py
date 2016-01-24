'''
Created on Nov 16, 2015

@author: ad23883
@todo: 
'''
from Commute.ParseCommuteData import parseCommuteData
from Commute.CommuteData import getCommuteData
from utils import *
from collections import OrderedDict

def processCommuteData():
    print '    Started Processing Commute Data'
    
    fileName = "Master-Commute_Data-2015"
    entries = OrderedDict()
    
    commuteData1, commuteData2, commuteData3, commuteData4 = getCommuteData()
    
    df1 = parseCommuteData(commuteData1)
    df2 = parseCommuteData(commuteData2)
    df3 = parseCommuteData(commuteData3)
    df4 = parseCommuteData(commuteData4)
    frames = [df1,df2,df3,df4]
    entries['Commute-Data'] = pd.concat(frames, ignore_index=True)
    
    populateMaster(os.path.join(commuteDataLocation, fileName+ext), entries)
    
    print '    Done Processing Commute Data\n'