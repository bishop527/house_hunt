'''
Created on Nov 16, 2015

@author: ad23883
@todo: 
'''

import School.ParseSchoolData as parse
from School.SchoolSiteData import downloadSchoolData
from utils import *
from collections import OrderedDict
from School.ParseSchoolData import prepSchoolTownRankData,\
    prepSchoolDistrictRankData

def processSchoolData():
    print "    Started Processing School Data"
    
    fileName = "Master-School_Data-2015.xlsx"
    dataLocation = 'data/school/'
    entries = OrderedDict()
    
    downloadSchoolData()
       
    entries['Admin-School'] = parse.parseSchoolAdminData()
    populateMaster(dataLocation+fileName, entries)
       
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
    # """Not sure what data is relevant so not adding to Master yet"""
#     entries['SPED-Compliance'] = parse.parseSPEDComplianceData()
#     entries['Teacher-Salary'] = parse.parseTeacherSalaryData()
    #entries['Rank-School'] = prepSchoolTownRankData()
    #entries['Rank-District'] = prepSchoolDistrictRankData()     
    entries['Rank-District'] = parse.parseSchoolDistrictRankData()
    populateMaster(dataLocation+fileName, entries)

    
    print "    Done Processing School Data\n"