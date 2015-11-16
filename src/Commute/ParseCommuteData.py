'''
Created on Nov 16, 2015

@author: ad23883
@todo: 
'''
import utils
import pandas as pd

dataLocation = "data/commute/"
ext = ".xlsx"

def parseCommuteData(data):
    print '            Parsing Commute Data'
    columns = ['Town', 'Distance to Work', 'Min to Work']
    rows = []
    
    for row in range(len(data["rows"])):
        origin = str(data['origin_addresses'][row]).split(',')[0]
        destination = data['destination_addresses'][0]
        duration = utils.convertToMin(str(data['rows'][row]['elements'][0]['duration']['text']))
        distance = str(data['rows'][row]['elements'][0]['distance']['text']).split(' ')[0]
        rows.append([origin, distance, duration])
   
    df = pd.DataFrame(rows, columns = columns)
    return df