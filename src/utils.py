'''
Created on Nov 4, 2015

@author: AD23883
'''
import pandas as pd
import platform
import os
import pwd
import urllib2

"""
Exporting data from the profiles.doe.mass.edu site does not save data as
true Excel files. This mehtod will save the data as an xls file so it 
can be used by libraries such as openpyxl and xlrd.
"""   
def convertToXLS(fileName, fileLocation, index = None, header = None, skiprows = None):
    """ Convert to true xls file """
    dfs = pd.read_html(fileLocation+fileName, index_col=index, skiprows=skiprows, header=header, thousands=None, )[-1]
    writer = pd.ExcelWriter(fileLocation+fileName, engine="openpyxl")
    dfs.to_excel(writer,"Sheet1")
    writer.save()
    
def setProxy():
    print "Turning on proxy"
    proxy = urllib2.ProxyHandler({'http' : 'llproxy.llan.ll.mit.edu:8080'})
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)
        
def setCurrDir():
    user = pwd.getpwuid(os.getuid())[0]
    
    if platform.system() == "Darwin":
        os.chdir("/Users/"+user+"/workspace/house_hunt/")
        print "Changed directory to /Users/"+user+"/workspace/house_hunt/"
    elif platform.system() == "Windows":
        os.chdir("c:\\Users\\"+user+"\\workspace\\house_hunt\\")
        print "Changed directory to c:\\Users\\"+user+"\\workspace\\house_hunt\\"
        