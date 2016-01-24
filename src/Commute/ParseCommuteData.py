'''
Created on Nov 16, 2015

@author: ad23883
@todo: 
'''
from utils import *
import pandas as pd

def parseCommuteData(data):
    print '            Parsing Commute Data'
    columns = ['House', 'Distance to Work', 'Min to Work', TRAFFIC_MODEL+' traffic']
    rows = []
    
    for row in range(len(data["rows"])):
        origin = str(data['origin_addresses'][row]).split(',')[0]
        destination = data['destination_addresses'][0]
        duration = convertToMin(str(data['rows'][row]['elements'][0]['duration']['text']))
        duration_in_traffic = convertToMin(str(data['rows'][row]['elements'][0]['duration_in_traffic']['text']))
        distance = str(data['rows'][row]['elements'][0]['distance']['text']).split(' ')[0]
        rows.append([origin, distance, duration, duration_in_traffic])
   
    df = pd.DataFrame(rows, columns = columns)
    return df