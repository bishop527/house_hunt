import School.ParseSchoolData as parse
from School.SchoolSiteData import downloadSchoolData
from utils import *
from collections import OrderedDict

fileName = "house_hunting-School_Data-2015.xlsx"

setCurrDir()
entries = OrderedDict()
setProxy()

downloadSchoolData()

entries['School_Admin'] = parse.parseAdminData()
entries['Accountability-District'] = parse.parseAccountDistrictData()
entries['Accountability-School'] = parse.parseAccountSchoolData()   
entries['Class_Size-District'] = parse.parseClassSizeDistrictData()
entries['Class_Size-School'] = parse.parseClassSizeSchoolData()
entries['Dropout-District'] = parse.parseDropoutDistrictData()    
entries['Dropout-School'] = parse.parseDropoutSchoolData()
entries['GraduationRates-District'] = parse.parseGraduationRateDistrictData()
entries['GraduationRates-School'] = parse.parseGraduationRateSchoolData()
entries['HigherEd-District'] = parse.parseHigherEdDistrictData()
entries['HigherEd-School'] = parse.parseHigherEdSchoolData()
entries['MCAS-District'] = parse.parseMCASDistrictData()
entries['MCAS-School'] = parse.parseMCASSchoolData()   
entries['SAT-District'] = parse.parseSATDistrictData()
entries['SAT-School'] = parse.parseSATSchoolData()
entries['SPED-Performance'] = parse.parseSPEDPerfData()
# # """Not sure what data is relevant so not adding to Master yet"""
# entries['SPED-Compliance'] = parse.parseSPEDComplianceData()
entries['Teacher-Salary'] = parse.parseTeacherSalaryData()

populateMaster(fileName, entries)
print "Done Adding School Data"