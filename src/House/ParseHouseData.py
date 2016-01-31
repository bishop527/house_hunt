'''
Created on Nov 10, 2015

@author: ad23883
@todo: 
'''
import pandas as pd
from House.HouseData import townExists, taxRateLookup
from utils import *

'''
Takes the town_zip.xls file, combines multiple zips for each town.
Pulls county for each town.
Looks up tax rate by town name.
Saves House, zips, county, and tax rate to the town_admin_data-2015.xlsx file 
'''
def parseTownAdminData():
    print '        Parsing House Admin Data'
    currTown = ''
    zips = ''
    data = []
    county = ''
    columns = ['Town', 'Zip Codes', 'County', 'Tax Rate']
    
    fileName = 'town_zips'
    ws = pd.ExcelFile(os.path.join(houseDataLocation, fileName+ext)).parse('Sheet1')
    ws.sort_values(by="Town", inplace=True)

    for row in range(len(ws)):
        zipCode = str(ws.iloc[row, 0]).strip()
        # leading zero's are stripped off for some reason. So need to re-add them
        if len(zipCode) == 4:
            zipCode= '0'+zipCode
        zips = zips+zipCode +','.strip()
        town = ws.iloc[row, 1]
        
        if not townExists(town):
            print town, ' is not in the list'
            
        taxRate = taxRateLookup(town)
        # check for multiple zips per town
        if town == currTown:
            if row < (len(ws)-1): 
                if town != ws.iloc[row+1, 1]:
                    data.append([town, zips, county, taxRate])
                    zips = ''
            # last row, append the data
            else:
                data.append([town, zips, county, taxRate])
        else:
            currTown = town
            county = ws.iloc[row, 2]
            if row < (len(ws)-1):
                if town != ws.iloc[row+1, 1]:
                    data.append([town, zips, county, taxRate])
                    zips = ''
            # last row, append the data
            else:
                data.append([town, zips, county, taxRate])
    
    df = pd.DataFrame(data, columns=columns)
    writer = pd.ExcelWriter(os.path.join(houseDataLocation, 'Town_Admin-2015'+ext), engine="openpyxl")
    df.to_excel(writer,"Sheet1")
    writer.save()
    
    return df

'''
This method parses the data in the MLS spreadsheet.
Currently the only way of obtaining this spreadsheet is from the realtor as a word doc.
The word doc is manually converted to a spreadsheet. The current version of the data
is from August 2015.
'''
def parseMLSHouseData(MLS_DATA_FILE):
    fileName = MLS_DATA_FILE
    columns = ['Town', 'Tax Rate', 'Median Sales Price', 'Tax Cost']
    data = []
    
    houseData = pd.read_excel(os.path.join(houseDataLocation, fileName+ext), header=0)
    houseData.sort_values(by='Town', inplace=True)
    
    for row in range(len(houseData)):
        town = houseData.iloc[row, 0]
        medSalePrice = houseData.iloc[row, 3]
        taxRate = taxRateLookup(town)
        taxCost = round(taxRate*(medSalePrice/1000), 2)
        
        data.append([town, taxRate, medSalePrice, taxCost])
        
        #In for debugging, can be removed
        if not townExists(town):
            print 'MLS Town', town, 'not in Town List'
        
    df = pd.DataFrame(data, columns=columns)
    
    return df