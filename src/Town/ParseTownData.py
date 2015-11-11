'''
Created on Nov 10, 2015

@author: ad23883
'''
import json
import pandas as pd
import utils

dataLocation = "data/town/"
ext = ".xlsx"

def parseCommuteData(data):
    #data = json.load(data)
    columns = ['Town', 'Distance to Work', 'Min to Work']
    rows = []
    
    for row in range(len(data["rows"])):
        origin = str(data['origin_addresses'][row]).split(',')[0]
        destination = data['destination_addresses'][0]
        duration = str(data['rows'][row]['elements'][0]['duration']['text']).split(' ')[0]
        distance = str(data['rows'][row]['elements'][0]['distance']['text']).split(' ')[0]
        rows.append([origin, distance, duration])
   
    df = pd.DataFrame(rows, columns = columns)
    return df