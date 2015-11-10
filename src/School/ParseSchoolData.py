import utils
import pandas as pd

dataLocation = "data/"
ext = ".xlsx"


"""
Parse the relevant information out of the data received from the admin site
Current relevant fields are:
    Town
    School Name
    Address
    School Type
    Grades

This method will ignore no-op (not operational) schools
This methid defaults to parsing data from 2015
""" 
def parseAdminData(year = "2015"):
    print "Started parsing Admin Data"
    fileName = "admin-"+year+ext
    columns = ['Town', 'School Name', 'School Type', 'School Address', 'Grades']
    rows = []
            
    """ Convert to true xls file """  
    utils.convertToXLS(fileName, dataLocation, 7, 0)
    
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):
        town = ws.iloc[row, 0]
        school_name = ws.iloc[row, 1]
        school_code = ws.iloc[row, 2]
        school_type = ws.iloc[row, 3]
        function = ws.iloc[row, 4]
        contact_name = ws.iloc[row, 5]
        address = ws.iloc[row, 6]
        address2 = ws.iloc[row, 7]
        state = ws.iloc[row, 8]
        zip = ws.iloc[row, 9]
        contact_phone = ws.iloc[row, 10]
        contact_fax = ws.iloc[row, 11]
        grades = str(ws.iloc[row, 12])
        
        # skip no-op schools        
        if grades != 'nan':
            rows.append([town, school_name, school_type, address, grades])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseAccountDistrictData(year="2014"):
    print "Started parsing Accountability District Data"
    fileName = "account-district-"+year+ext
    columns = ['District', 'Level', 'Notes']
    rows = []

    """ Convert to true xls """    
    utils.convertToXLS(fileName, dataLocation, skiprows=2)        
#     
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):
        district = ws.iloc[row, 0]
        school_code = ws.iloc[row, 1]
        level = ws.iloc[row, 2]
        notes = ws.iloc[row, 3]
        num_students = ws.iloc[row, 4]
        highNeed_students = ws.iloc[row, 5]
        
        rows.append([district, level, notes])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseAccountSchoolData(year="2014"):
    print "Started parsing Accountability School Data"
    fileName = "account-school-"+year+ext
    columns = ['Town', 'School', 'Type', 'Level', 'Notes', 'Percentile']
    rows = []

    """ Convert to true xls file """    
    utils.convertToXLS(fileName, dataLocation, skiprows=2)        
   
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' not in ws.iloc[row,0]:
            # hack because this entry has 2 ' - '
            if ws.iloc[row,0] == "Boston - ELC - West Zone":
                town = "Boston"
                school = "ELC-West Zone"
            else:
                town, school = ws.iloc[row, 0].split(' - ')
            
            school_code = ws.iloc[row, 1]
            level = ws.iloc[row, 2]
            notes = ws.iloc[row, 3]
            type = ws.iloc[row, 4]
            percentile = ws.iloc[row, 5]
            
            rows.append([town, school, type, level, notes, percentile])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseClassSizeDistrictData(year='2014'):
    print "Started parsing Class Size District Data"
    fileName = "class_size-district-"+year+ext
    columns = ['District', 'Avg Size', 'SPED %']
    rows = []

    """ Convert to true xls file """    
    utils.convertToXLS(fileName, dataLocation, header=0)        
   
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):        
        district = ws.iloc[row, 0]
        school_code = ws.iloc[row, 1]
        total_classes = ws.iloc[row, 2]
        avg_size = ws.iloc[row, 3]
        num_students = ws.iloc[row, 4]
        female_perc = ws.iloc[row, 5]
        male_perc = ws.iloc[row, 6]
        lep_perc = ws.iloc[row, 7]
        sped_perc = ws.iloc[row, 8]
        low_income = ws.iloc[row, 9]
            
        rows.append([district, avg_size, sped_perc])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseClassSizeSchoolData(year='2014'):
    print "Started parsing Class Size School Data"
    
    fileName = "class_size-school-"+year+ext
    columns = ['Town', 'School', 'Total Classes', '# Students', 'Avg Size']
    rows = []

    """ Convert to true xls file """    
    utils.convertToXLS(fileName, dataLocation, header=0)        
   
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' not in ws.iloc[row,0]:
            # hack because this entry has 2 ' - '
            if ws.iloc[row,0] == "Boston - ELC - West Zone":
                town = "Boston"
                school = "ELC-West Zone"
            else:
                town, school = ws.iloc[row, 0].split(' - ')
            
            total_classes = ws.iloc[row, 2]
            avg_size = ws.iloc[row, 3]
            num_students = ws.iloc[row, 4]
            african_perc = ws.iloc[row,5]
            asian_perc = ws.iloc[row,6]
            hisp_perc = ws.iloc[row,7]
            white_perc = ws.iloc[row,8]
            native_perc = ws.iloc[row,9]
            island_perc = ws.iloc[row,10]
            multi_perc = ws.iloc[row,11]
            
            rows.append([town, school, total_classes, num_students, avg_size])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseDropoutDistrictData(year="2014"):
    print "Started parsing Dropout District Data"
    fileName = "dropout-district-"+year+ext
    columns = ['District', '# Enrolled', 'Total Drop', 'Total Drop %']
    rows = []

    """ Convert to true xls """    
    utils.convertToXLS(fileName, dataLocation, skiprows = 1, header=0)        
#     
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):
        district = ws.iloc[row, 0]
        school_code = ws.iloc[row, 1]
        num_enrolled = ws.iloc[row, 2]
        total_drop = ws.iloc[row, 3]
        perc_total_drop = ws.iloc[row, 4]
        perc_gr9_drop = ws.iloc[row, 5]
        perc_gr10_drop = ws.iloc[row, 6]
        perc_gr11_drop = ws.iloc[row, 7]           
        perc_gr12_drop = ws.iloc[row, 8]
             
        rows.append([district, num_enrolled, total_drop, perc_total_drop])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseDropoutSchoolData(year="2014"):
    print "Started parsing Dropout School Data"
    fileName = "dropout-school-"+year+ext
    columns = ['Town', 'School', '# Enrolled', 'Total Drop', 'Total Drop %']
    rows = []

    """ Convert to true xls file """    
    utils.convertToXLS(fileName, dataLocation, skiprows=1, header=0)        
   
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' not in ws.iloc[row,0]:
            # hack because this entry has 2 ' - '
            if ws.iloc[row,0] == "Boston - ELC - West Zone":
                town = "Boston"
                school = "ELC-West Zone"
            else:
                town, school = ws.iloc[row, 0].split(' - ')
            
            school_code = ws.iloc[row, 1]
            num_enrolled = ws.iloc[row, 2]
            total_drop = ws.iloc[row, 3]
            perc_total_drop = ws.iloc[row, 4]
            perc_gr9_drop = ws.iloc[row, 5]
            perc_gr10_drop = ws.iloc[row, 6]
            perc_gr11_drop = ws.iloc[row, 7]           
            perc_gr12_drop = ws.iloc[row, 8]
            
            rows.append([town, school, num_enrolled, total_drop, perc_total_drop])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseHigherEdDistrictData(year="2013"):
    print "Started parsing Higher Education District Data"
    fileName = "higher_edu-district-"+year+ext
    columns = ['District', '# Grads', '# to College', '% to College']
    rows = []

    """ Convert to true xls """    
    utils.convertToXLS(fileName, dataLocation, header=0)        
#     
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):
        district = ws.iloc[row, 0]
        school_code = ws.iloc[row, 1]
        num_hs_grad = ws.iloc[row, 2]
        num_to_coll = ws.iloc[row, 3]
        perc_to_coll = ws.iloc[row, 4]
        perc_priv_2yr = ws.iloc[row, 5]
        perc_priv_4yr = ws.iloc[row, 6]
        perc_pub_2yr = ws.iloc[row, 7]           
        perc_pub_4yr = ws.iloc[row, 8]
        perc_MA_cc = ws.iloc[row, 9]
        perc_MA_state = ws.iloc[row, 10]
        perc_UMass = ws.iloc[row, 11]
            
        rows.append([district, num_hs_grad, num_to_coll, perc_to_coll])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseHigherEdSchoolData(year="2013"):
    print "Started parsing Higher Ed School Data"
    fileName = "higher_edu-school-"+year+ext
    columns = ['Town', 'School', '# Grads', '# to College', '% to College']
    rows = []

    """ Convert to true xls file """    
    utils.convertToXLS(fileName, dataLocation, header=0)        
   
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' not in ws.iloc[row,0]:
            # hack because this entry has 2 ' - '
            if ws.iloc[row,0] == "Boston - ELC - West Zone":
                town = "Boston"
                school = "ELC-West Zone"
            else:
                town, school = ws.iloc[row, 0].split(' - ')
            
            school_code = ws.iloc[row, 1]
            num_hs_grad = ws.iloc[row, 2]
            num_to_coll = ws.iloc[row, 3]
            perc_to_coll = ws.iloc[row, 4]
            perc_priv_2yr = ws.iloc[row, 5]
            perc_priv_4yr = ws.iloc[row, 6]
            perc_pub_2yr = ws.iloc[row, 7]           
            perc_pub_4yr = ws.iloc[row, 8]
            perc_MA_cc = ws.iloc[row, 9]
            perc_MA_state = ws.iloc[row, 10]
            perc_UMass = ws.iloc[row, 11]
                
            rows.append([town, school, num_hs_grad, num_to_coll, perc_to_coll])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseGraduationRateDistrictData(year="2014"):
    print "Started parsing Graduation Rates District Data"
    fileName = "grad_rates-district-"+year+ext
    columns = ['District', '# Students', '% Graduated']
    rows = []

    """ Convert to true xls """    
    utils.convertToXLS(fileName, dataLocation, header=0)        
#     
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):
        district = ws.iloc[row, 0]
        school_code = ws.iloc[row, 1]
        num_students = ws.iloc[row, 2]
        perc_grad = ws.iloc[row, 3]
        perc_in_school = ws.iloc[row, 4]
        perc_non_grad_complete = ws.iloc[row, 5]
        perc_ged = ws.iloc[row, 6]
        perc_dropped = ws.iloc[row, 7]           
        perc_excluded = ws.iloc[row, 8]
            
        rows.append([district, num_students, perc_grad])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseGraduationRateSchoolData(year="2014"):
    print "Started parsing Graduation Rates School Data"
    fileName = "grad_rates-school-"+year+ext
    columns = ['Town', 'School', '# Students', '% Grad']
    rows = []

    """ Convert to true xls file """    
    utils.convertToXLS(fileName, dataLocation, header=0)        
   
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' not in ws.iloc[row,0]:
            # hack because this entry has 2 ' - '
            if ws.iloc[row,0] == "Boston - ELC - West Zone":
                town = "Boston"
                school = "ELC-West Zone"
            else:
                town, school = ws.iloc[row, 0].split(' - ')
            
            school_code = ws.iloc[row, 1]
            num_students = ws.iloc[row, 2]
            perc_grad = ws.iloc[row, 3]
            perc_in_school = ws.iloc[row, 4]
            perc_non_grad_complete = ws.iloc[row, 5]
            perc_ged = ws.iloc[row, 6]
            perc_dropped = ws.iloc[row, 7]           
            perc_excluded = ws.iloc[row, 8]
                
            rows.append([town, school, num_students, perc_grad])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseMCASDistrictData(year="2015"):
    print "Started parsing MCAS District Data"
    fileName = "mcas-district-"+year+ext
    columns = ['District', '# Students', 'Subject', '# Adv', '% Adv', '# Prof', '% Prof', '# NI', '% NI']
    rows = []

    """ Convert to true xls """    
    utils.convertToXLS(fileName, dataLocation, header=0)        
#     
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):
        district = ws.iloc[row, 0]
        school_code = ws.iloc[row, 1]
        subject = ws.iloc[row, 2]
        num_prof_adv = ws.iloc[row, 3]
        perc_prof_adv = ws.iloc[row, 4]
        num_adv = ws.iloc[row, 5]
        perc_adv = ws.iloc[row, 6]
        num_prof = ws.iloc[row, 7]           
        perc_prof = ws.iloc[row, 8]
        num_NI = ws.iloc[row, 9]
        perc_NI = ws.iloc[row, 10]
        num_WF = ws.iloc[row, 11]
        perc_WF = ws.iloc[row, 12]
        num_students = ws.iloc[row, 13]
        cpi = ws.iloc[row, 14]
        sgp = ws.iloc[row, 15]
        num_sgp = ws.iloc[row, 16]    
        
        rows.append([district, num_students, subject, num_adv, perc_adv, num_prof, perc_prof, num_NI, perc_NI])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseMCASSchoolData(year="2015"):
    print "Started parsing MCAS School Data"
    fileName = "mcas-school-"+year+ext
    columns = ['Town', 'School', '# Students', 'Subject', '# Adv', '% Adv', '# Prof', '% Prof', '# NI', '% NI']
    rows = []

    """ Convert to true xls file """    
    utils.convertToXLS(fileName, dataLocation, header=0)        
   
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' not in ws.iloc[row,0]:
            # hack because these entry has 2 ' - '
            if ws.iloc[row,0] == "Boston - ELC - West Zone":
                town = "Boston"
                school = "ELC-West Zone"
            elif "Easton - Richardson" in ws.iloc[row,0]:
                town = "Easton"
                school = "Olmstead School"
            else:
                town, school = ws.iloc[row, 0].split(' - ')
            
            school_code = ws.iloc[row, 1]
            subject = ws.iloc[row, 2]
            num_prof_adv = ws.iloc[row, 3]
            perc_prof_adv = ws.iloc[row, 4]
            num_adv = ws.iloc[row, 5]
            perc_adv = ws.iloc[row, 6]
            num_prof = ws.iloc[row, 7]           
            perc_prof = ws.iloc[row, 8]
            num_NI = ws.iloc[row, 9]
            perc_NI = ws.iloc[row, 10]
            num_WF = ws.iloc[row, 11]
            perc_WF = ws.iloc[row, 12]
            num_students = ws.iloc[row, 13]
            cpi = ws.iloc[row, 14]
            sgp = ws.iloc[row, 15]
            num_sgp = ws.iloc[row, 16]    
            
            rows.append([town, school, num_students, subject, num_adv, perc_adv, num_prof, perc_prof, num_NI, perc_NI])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseSATDistrictData(year="2015"):
    print "Started parsing SAT District Data"
    fileName = "sat-district-"+year+ext
    columns = ['District', '# Tests', 'Reading', 'Writing', 'Math']
    rows = []

    """ Convert to true xls """    
    utils.convertToXLS(fileName, dataLocation, header=0)        
#     
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):
        district = ws.iloc[row, 0]
        school_code = ws.iloc[row, 1]
        tests_taken = ws.iloc[row, 2]
        reading = ws.iloc[row, 3]
        writing = ws.iloc[row, 4]
        math = ws.iloc[row, 5]
               
        rows.append([district, tests_taken, reading, writing, math])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseSATSchoolData(year="2015"):
    print "Started parsing SAT School Data"
    fileName = "sat-school-"+year+ext
    columns = ['Town', 'School', 'Tests Taken', 'Reading', 'Writing', 'Math']
    rows = []

    """ Convert to true xls file """    
    utils.convertToXLS(fileName, dataLocation, header=0)        
   
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' not in ws.iloc[row,0]:
            # hack because these entry has 2 ' - '
            if ws.iloc[row,0] == "Boston - ELC - West Zone":
                town = "Boston"
                school = "ELC-West Zone"
            elif "Easton - Richardson" in ws.iloc[row,0]:
                town = "Easton"
                school = "Olmstead School"
            else:
                town, school = ws.iloc[row, 0].split(' - ')
            
            school_code = ws.iloc[row, 1]
            tests_taken = ws.iloc[row, 2]
            reading = ws.iloc[row, 3]
            writing = ws.iloc[row, 4]
            math = ws.iloc[row, 5]
               
            rows.append([town, school, tests_taken, reading, writing, math])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseSPEDPerfData(year="2014"):
    print "Started parsing SPED Performance Data"
    fileName = "sped-performance-"+year+ext
    columns = pd.MultiIndex.from_tuples([('District', ''),
                                         ('SPED Grad Rate', 'Cohort #'), ('SPED Grad Rate', 'Grad #'), ('SPED Grad Rate', 'Grad %'), 
                                         ('SPED Dropout', 'Enrolled'), ('SPED Dropout', '# Dropped'), ('SPED Dropout', '% Dropped'),
                                         ('Ages 6-21', '# Students'), ('Ages 6-21', '# Full Incl'), ('Ages 6-21', '% Full Incl'),
                                         ('Parent Involvement', 'Period'), ('Parent Involvement', '# Meet Std'), ('Parent Involvement', '% Meet Std')
                                         ])
    rows = []

    """ Convert to true xls """    
    utils.convertToXLS(fileName, dataLocation, skiprows=2)        
#     
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):
        district = ws.iloc[row, 0]
        school_code = ws.iloc[row, 1]
        ind1_num_cohort = ws.iloc[row, 2]
        ind1_num_grad = ws.iloc[row, 3]
        ind1_perc_grad = ws.iloc[row, 4]
        ind2_num_enrolled = ws.iloc[row, 5]
        ind2_num_dropped = ws.iloc[row, 6]
        ind2_perc_dropped = ws.iloc[row, 7]
        ind5_num_students = ws.iloc[row, 8]
        ind5_num_full_incl = ws.iloc[row, 9]
        ind5_perc_full_incl = ws.iloc[row, 10]
        ind6_num_students = ws.iloc[row, 11]
        ind6_num_full_incl = ws.iloc[row, 12]
        ind6_perc_full_incl = ws.iloc[row, 13]
        ind7_cohort_year = ws.iloc[row, 14]
        ind7_growth = ws.iloc[row, 15]
        ind8_period = ws.iloc[row, 16]
        ind8_num_meet_std = ws.iloc[row, 17]
        ind8_perc_meet_std = ws.iloc[row, 18]
        ind14_year = ws.iloc[row, 19]
        ind14_num_students = ws.iloc[row, 20]
        ind14_dist_rate = ws.iloc[row, 21]

        rows.append([district, 
                     ind1_num_cohort, ind1_num_grad, ind1_perc_grad, 
                     ind2_num_enrolled, ind2_num_dropped, ind2_perc_dropped,
                     ind6_num_students, ind6_num_full_incl, ind6_perc_full_incl,
                     ind8_period, ind8_num_meet_std, ind8_perc_meet_std])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseSPEDComplianceData(year="2014"):
    print "Started parsing SPED Compliance Data"
    fileName = "sped-compliance-"+year+ext
    columns = pd.MultiIndex.from_tuples([('District', )])
    rows = []

    """ Convert to true xls """    
    utils.convertToXLS(fileName, dataLocation, skiprows=2)        
#     
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):
        district = ws.iloc[row, 0]
        school_code = ws.iloc[row, 1]
        ind4a_num_students = ws.iloc[row, 2]
        ind4a_num_susp = ws.iloc[row, 3]
        ind4a_perc_susp = ws.iloc[row, 4]
        ind4b_discrepancy = ws.iloc[row, 5]
        ind4b_ppp_contrib = ws.iloc[row, 6]
        ind9_disproportionate_repr = ws.iloc[row, 7]
        ind10_disproportionate_repr = ws.iloc[row, 8]
        ind11_year = ws.iloc[row, 9]
        ind11_num_eval_compl = ws.iloc[row, 10]
        ind11_distr_rate = ws.iloc[row, 11]
        ind12_year = ws.iloc[row, 12]
        ind12_ref_partC = ws.iloc[row, 13]
        ind12_iep_by_num = ws.iloc[row, 14]
        ind12_iep_by_perc = ws.iloc[row, 15]
        ind13_year = ws.iloc[row, 16]
        ind13_num_records_compliant = ws.iloc[row, 17]
        ind13_dist_rate = ws.iloc[row, 18]

        rows.append([district])
        
    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseTeacherSalaryData(year="2013"):
    print "Started parsing Teacher Salary Data"
    fileName = "teacher-salary-"+year+ext
    columns = ['District', 'Salary Total', 'Avg Salary', 'FTE Count']
    rows = []

    """ Convert to true xls """    
    utils.convertToXLS(fileName, dataLocation, header=0)        
#     
    """ Open new xls file """
    ws = pd.read_excel(dataLocation+fileName, 0)
     
    for row in range(len(ws)):
        district = ws.iloc[row, 0]
        school_code = ws.iloc[row, 1]
        salary_total = ws.iloc[row, 2]
        avg_salary = ws.iloc[row, 3]
        fte_count = ws.iloc[row, 4]
               
        rows.append([district, salary_total, avg_salary, fte_count])

    df = pd.DataFrame(rows, columns = columns)
    
    return df
