import pandas as pd
import openpyxl as pyxl
import os.path
import School.ParseSchoolData as parse
from School.SchoolSiteData import downloadSchoolData
import utils

masterFile = "house_hunting-2015.xlsx"
utils.setCurrDir()
dataLocation = "data/" 

""" 
Appends the given DataFrame with the master workbook and names the worksheet the given sheetName 
"""
def populateMaster(sheetName, data):
    print "Adding", sheetName, "to masterFile"
    if os.path.isfile(masterFile):
        book = pyxl.load_workbook(masterFile)
        writer = pd.ExcelWriter(masterFile, engine="openpyxl")
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
    else:
        writer = pd.ExcelWriter(masterFile)
        
    data.to_excel(writer, sheetName)
    writer.save()

downloadSchoolData()

df = parse.parseAdminData()
populateMaster("School_Admin", df)
   
df = parse.parseAccountDistrictData()
populateMaster("Accountability-District", df)
   
df = parse.parseAccountSchoolData()
populateMaster("Accountability-School", df)
  
df = parse.parseClassSizeDistrictData()
populateMaster("Class_Size-District", df)
  
df = parse.parseClassSizeSchoolData()
populateMaster("Class_Size-School", df)
   
df = parse.parseDropoutDistrictData()
populateMaster("Dropout-District", df)
   
df = parse.parseDropoutSchoolData()
populateMaster("Dropout-School", df)
  
df = parse.parseHigherEdDistrictData()
populateMaster("HigherEd-District", df)
  
df = parse.parseHigherEdSchoolData()
populateMaster("HigherEd-School", df)
  
df = parse.parseGraduationRateDistrictData()
populateMaster("GraduationRates-District", df)
  
df = parse.parseGraduationRateSchoolData()
populateMaster("GraduationRates-School", df)
  
df = parse.parseMCASDistrictData()
populateMaster("MCAS-District", df)
  
df = parse.parseMCASSchoolData()
populateMaster("MCAS-School", df)
  
df = parse.parseSATDistrictData()
populateMaster("SAT-District", df)
  
df = parse.parseSATSchoolData()
populateMaster("SAT-School", df)

df = parse.parseSPEDPerfData()
populateMaster("SPED-Performance", df)
# 
# df = parse.parseSPEDComplianceData()
# """Not sure what data is relevant so not adding to Master yet"""
# #populateMaster("SPED-Compliance", df)

df = parse.parseTeacherSalaryData()
populateMaster("Teacher-Salary", df)

print "Done"