'''
Created on Nov 10, 2015

@author: ad23883
'''
import pandas as pd
import utils
import TownData

dataLocation = "data/town/"
ext = ".xlsx"

def parseCommuteData(data):
    print 'Parsing Commute Data'
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
Takes the town_zip.xls file, combines multiple zips for each town.
Pulls county for each town.
Looks up tax rate by town name.
Saves Town, zips, county, and tax rate to the town_admin_data-2015.xlsx file 
'''
def parseTownAdminData():
    print 'Parsing Town Admin Data'
    currTown = ''
    zips = ''
    rows = []
    county = ''
    columns = ['Town', 'Zips', 'County', 'Tax Rate']
    
    fileName = 'town_zips.xlsx'
    ws = pd.ExcelFile(dataLocation+fileName).parse('Sheet1')
    ws.sort_values(by="Town", inplace=True)

    for row in range(len(ws)):
        zipCode = str(ws.iloc[row, 0]).strip()
        # leading zero's are stripped off for some reason. So need to re-add them
        if len(zipCode) == 4:
            zipCode= '0'+zipCode
        zips = zips+zipCode +','.strip()
        town = ws.iloc[row, 1]
            
        taxRate = TownData.taxRateLookup(town)
        # check for multiple zips per town
        if town == currTown:
            if row < (len(ws)-1): 
                if town != ws.iloc[row+1, 1]:
                    rows.append([town, zips, county, taxRate])
                    zips = ''
            # last row, append the data
            else:
                rows.append([town, zips, county, taxRate])
        else:
            currTown = town
            county = ws.iloc[row, 2]
            if row < (len(ws)-1):
                if town != ws.iloc[row+1, 1]:
                    rows.append([town, zips, county, taxRate])
                    zips = ''
            # last row, append the data
            else:
                rows.append([town, zips, county, taxRate])
    
    df = pd.DataFrame(rows, columns=columns)
    writer = pd.ExcelWriter(dataLocation+'Town_Admin-2015.xlsx', engine="openpyxl")
    df.to_excel(writer,"Sheet1")
    writer.save()
    
    return df