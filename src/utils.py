'''
Created on Nov 4, 2015

@author: AD23883

'''
import os.path
import urllib
from constants import *
import pandas as pd

proxy_on = False

""" 
Appends the given DataFrame with the master workbook and names the worksheet the given sheetName 
"""
def populateMaster(fileName, df):
    for sheetName, data in df.items():
        print("            Adding", sheetName, "to", fileName)
        if os.path.isfile(fileName):
            with pd.ExcelWriter(fileName, engine='openpyxl', mode="a", if_sheet_exists="replace") as writer:
                data.to_excel(writer, sheet_name=sheetName, index=True)
        else:
            writer = pd.ExcelWriter(fileName, engine='odf')
            data.to_excel(writer, sheet_name=sheetName, index=False)
            writer.save()

"""
Utility function to convert string of hours and minutes into minutes.
For example, string of 1 hour 3 min will return 63
duration string passed in is expected to be in 1 of the following formats
# hour # min
# hour
# min
"""
def convertToMin(duration):    
    min = 0
    fields = duration.split(' ')
    
    """ fields has hour and min """
    if len(fields) == 4:
        min = int(fields[0]) * 60 + int(fields[2])
    elif len(fields) == 2:
        if "hour" in fields[1]:
            min = int(fields[0]) * 60
        elif "min" in fields[1]:
            min = int(fields[0])
        else:
            "Encountered unknown format"
    return 	min

"""
Exporting data from the profiles.doe.mass.edu site does not save data as
true Excel files. This mehtod will save the data as an xls file so it 
can be used by libraries such as openpyxl and xlrd.
"""   
def convertToXLS(fileName, fileLocation, index = None, header = None, skiprows = None):
    """ Convert to true xls file """
    dfs = pd.read_html(os.path.join(fileLocation, fileName), index_col=index, skiprows=skiprows, header=header, thousands=None, )[-1]
    writer = pd.ExcelWriter(os.path.join(fileLocation, fileName), engine="openpyxl")
    dfs.to_excel(writer,"Sheet1")
    writer.save()
    
def setProxy(type='http'):
    print("Turning on", type, "proxy")
    proxy_on = True
    proxy = urllib.ProxyHandler({type : 'localhost:8080'})
    opener = urllib.build_opener(proxy)
    urllib.install_opener(opener)
        
# def setCurrDir():
#     user = pwd.getpwuid(os.getuid())[0]
#     
#     if platform.system() == "Darwin":
#         os.chdir("/Users/"+user+"/workspace/house_hunt/")
#         print "Changed directory to /Users/"+user+"/workspace/house_hunt/"
#     elif platform.system() == "Windows":
#         os.chdir("c:\\Users\\"+user+"\\workspace\\house_hunt\\")
#         print "Changed directory to c:\\Users\\"+user+"\\workspace\\house_hunt\\"

'''
Restrict score to no greater then maxScore and no less than MIN_SCORE
'''
def normalizeScore(score):
        
    if score > MAX_SCORE:
        score = MAX_SCORE
    elif score < MIN_SCORE:
        score = MIN_SCORE
    return score


'''
Parses out and returns zip codes from data/town_zips.xlsx
'''
def getMAZips():
    fileName = 'town_zips'
    zips = []

    data = pd.read_excel(os.path.join(HOUSE_DATA, fileName + EXT),
                         header=0)

    for zipCode in data.Zip:
        # Leading zero is stripped so need to re-add
        zips.append('0' + str(zipCode))

    return zips
