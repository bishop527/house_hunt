'''
Created on Nov 4, 2015

@author: AD23883
@todo: 
'''
import pandas as pd
#import platform
#import pwd
import urllib2
import openpyxl as pyxl
import os.path

MAX_SCORE = 10
MIN_SCORE = -10
MEDIAN_SCORE = 0

dataLocation = os.path.join('..', 'data')
houseDataLocation = os.path.join('..', 'data', 'house')
schoolDataLocation = os.path.join('..', 'data', 'school')
commuteDataLocation = os.path.join('..', 'data', 'commute')
townDataLocation = os.path.join('..', 'data', 'town')

ext = '.xlsx'

proxy_on = False

# seconds from 1 Jan 1970 to 2 May 2016 07:00 EST
DEPARTURE_TIME = 1462186800
TRAFFIC_MODEL = 'best_guess'
DESTINATION = '244 Wood St. Lexington, MA'
AVOID_TOLLS = ''

""" 
Appends the given DataFrame with the master workbook and names the worksheet the given sheetName 
"""
def populateMaster(fileName, df):
    for sheetName, data in df.iteritems():
        print "            Adding", sheetName, "to", fileName
        if os.path.isfile(fileName):
            book = pyxl.load_workbook(fileName)
            writer = pd.ExcelWriter(fileName, engine='openpyxl')
            writer.book = book
            writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        else:
            writer = pd.ExcelWriter(fileName, engine='openpyxl')    
        data.to_excel(writer, sheetName)
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
    print "Turning on", type, "proxy"
    proxy_on = True
    proxy = urllib2.ProxyHandler({type : 'llproxy.llan.ll.mit.edu:8080'})
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)
        
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
        