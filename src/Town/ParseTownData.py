'''
Created on Nov 10, 2015

@author: ad23883
@todo: 
'''
import pandas as pd
import TownData

dataLocation = "data/town/"
ext = ".xlsx"

'''
Takes the town_zip.xls file, combines multiple zips for each town.
Pulls county for each town.
Looks up tax rate by town name.
Saves Town, zips, county, and tax rate to the town_admin_data-2015.xlsx file 
'''
def parseTownAdminData():
    print '        Parsing Town Admin Data'
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
        
        if not TownData.townExists(town):
            print town, ' is not in the list'
            
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