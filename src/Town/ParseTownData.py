'''
Created on Nov 10, 2015

@author: ad23883
'''
import pandas as pd
import utils

dataLocation = "data/town/"
ext = ".xlsx"

def parseCommuteData(data):
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

'''
Takes the town-zip.xls file, combines multiple zips for each town, and pulls county for each town
Saves Town, zips, and county to the town_admin_data-2015.xlsx file 
'''
def parseTownAdminData():

    currTown = ''
    zip = ''
    rows = []
    county = ''
    columns = ['Town', 'Zips', 'County']
    
    fileName = 'town_zips.xlsx'
    ws = pd.ExcelFile(dataLocation+fileName).parse('Sheet1')
    ws.sort_values(by="Town", inplace=True)

    for row in range(len(ws)):
        town = ws.iloc[row, 1]
        # check for multiple zips per town
        if town == currTown:
            zip = zip + str(ws.iloc[row, 0]) +', '
            if row < (len(ws)-1) and town != ws.iloc[row+1, 1]:
                rows.append([town, zip, county])
                zip = ''
        else:
            currTown = town
            zip = zip + str(ws.iloc[row, 0]) +', '
            county = ws.iloc[row, 2]
            if row < (len(ws)-1) and town != ws.iloc[row+1, 1]:
                rows.append([town, zip, county])
                zip = ''
    
    return pd.DataFrame(rows, columns=columns)