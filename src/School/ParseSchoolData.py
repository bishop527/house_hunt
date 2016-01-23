'''
Created on Nov 16, 2015

@author: ad23883
@todo: 
'''
from utils import *
import pandas as pd

class SchoolData(object):

    def __init__(self, town, district, type, grades):
        self.town = town
        self.district = district
        self.type = type
        self.grades = grades

    def getTown(self):
        return self.town
    
    def getDistrictL(self):
        return self.district
    
    def getType(self):
        return self.type
    
    def getGrades(self):
        return self.grades
    
    def setTown(self, town):
        self.town = town
        
    def settype(self, type):
        self.type = type
    
    def setGrades(self, grades):
        self.grades = grades
        

regionalSchools = {'Acton-Boxborough': ['Acton', 'Boxborough'],
                   'Adams-Cheshire': ['Adams', 'Cheshire', 'Savoy'],
                   'Amherst-Pelham': ['Amherst', 'Leverett', 'Pelham', 'Shutesbury'],
                   'Ashburnham-Westminster':['Ashburnham', 'Westminster'],
                   'Athol-Royalston': ['Athol', 'Royalston'],
                   'Ayer Shirley School District': ['Ayer', 'Shirley'],
                   'Berkshire Hills': ['Great Barrington', 'Stockbridge', 'West Stockbridge'],
                   'Berlin-Boylston': ['Berlin','Boylston'],
                   'Blackstone-Millville':['Blackstone', 'Millville'],
                   'Bridgewater-Raynham': ['Bridgewater', 'Raynham'],
                   'Chesterfield-Goshen':['Chesterfield', 'Goshen'],
                   'Central Berkshire': ['Becket', 'Cummington', 'Dalton', 'Hindsdale', 'Peru', 'Washington', 'Windsor'],
                   'Concord-Carlisle': ['Concord', 'Carlisle'],
                   'Dennis-Yarmouth': ['Dennis', 'Yarmouth'],
                   'Dighton-Rehoboth': ['Dighton', 'Rehoboth'],
                   'Dover-Sherborn': ['Dover', 'Sherborn'],
                   'Dudley-Charlton': ['Dudley', 'Charlton'],
                   'Nauset': ['Brewster', 'Eastham', 'Orleans', 'Provincetown', 'Truro', 'Wellfleet'],
                   'Farmington River Reg': ['Otis', 'Sandisfield'],
                   'Freetown-Lakeville': ['Freetown', 'Lakeville'],
                   'Frontier': ['Conway', 'Deerfield', 'Sunderland', 'Whately'],
                   'Gateway': ['Blandford', 'Chester', 'Huntington', 'Middlefield', 'Montgomery', 'Russell', 'Worthington'],
                   'Groton-Dunstable':['Groton', 'Dunstable'],
                   'Gill-Montague':['Gill', 'Montague', 'Erving'],
                   'Hamilton-Wenham': ['Hamilton', 'Wenham'],
                   'Hampden-Wilbraham': ['Hampden', 'Wilbraham'],
                   'Hampshire': ['Chesterfield', 'Goshen', 'Southampton', 'Westhampton', 'Williamsburg'],
                   'Hawlemont': ['Charlemont', 'Hawley'],
                   'King Philip': ['Norfolk', 'Plainville', 'Wrentham'],
                   'Lee': ['Lee', 'Tyringham'],
                   'Lincoln-Sudbury': ['Lincoln', 'Sudbury'],
                   'Manchester Essex Regional': ['Essex', 'Manchester', 'Manchester-by-the-sea'],
                   "Martha's Vineyard": ['Chilmark', 'Edgartown', 'Aquinnah', 'Oak Bluffs', 'Tisbury', 'West Tisbury'],
                   'Masconomet': ['Boxford', 'Middleton', 'Topsfield'],
                   'Mendon-Upton': ['Mendon', 'Updton'],
                   'Mount Greylock': ['Lanesborough', 'Williamstown', 'New Ashford'],
                   'Monomoy Regional School District': ['Chatham', 'Harwich'],
                   'Mohawk Trail': ['Ashfield', 'Buckland', 'Charlemont', 'Colrain', 'Hawley', 'Heath', 'Plainfield', 'Rowe', 'Shelburne'],
                   'Narragansett': ['Phillipston', 'Templeton'],
                   'Nashoba': ['Bolton', 'Lancaster', 'Stow'],
                   'New Salem-Wendell': ['New Salem', 'Wendell'],
                   'Northboro-Southboro': ['Northboro', 'Northborough', 'Southboro', 'Southborough'],
                   'North Middlesex': ['Ashby', 'Pepperell', 'Townsend'],
                   'Old Rochester': ['Marion', 'Mattapoisett', 'Rochester'],
                   'Pentucket': ['Groveland', 'Merrimac', 'West Newbury'],
                   'Pioneer Valley': ['Bernardston', 'Leyden', 'Northfield', 'Warwick'],
                   'Quabbin': ['Barre', 'Enfield', 'Hardwick', 'Hubbardston', 'New Braintree', 'Oakham'],
                   'Ralph C Mahar': ['New Salem', 'Orange', 'Petersham', 'Wendell'],
                   'Silver Lake': ['Halifax', 'Kingston', 'Plympton'],
                   'Somerset-Berkley Regional School District': ['Somerset', 'Berkley'],
                   'Southern Berkshire': ['Alford', 'Egremont', 'Monterey', 'Mt Washington', 'New Marlborough', 'Sheffield'],
                   'Southwick-Tolland-Granville Regional School District': ['Southwick', 'Tolland', 'Granville'],
                   'Spencer-E Brookfield': ['East Brookfield', 'Spencer'],
                   'Tantasqua': ['Brimfield', 'Brookfield', 'Holland', 'Sturbridge', 'Wales'],
                   'Triton': ['Newbury', 'Rowley', 'Salisbury'],
                   'Up-Island Regional': ['Chilmark', 'Aquinnah', 'West Tisbury'],
                   'Wachusett': ['Holden', 'Paxton', 'Princeton', 'Rutland', 'Sterling'],
                   'Quaboag Regional': ['Warren', 'West Brookfield'],
                   'Whitman-Hanson': ['Hanson', 'Whitman']}

relevantDistricts = []
districtTownList = []

def findRelevantDistricts(ws):
    currDistrict = ''
    currGrades = []
    
    for row in range(len(ws)):
        town = ws.iloc[row, 0]
        district_name, school_name, school_type = getSchoolinfo(ws.iloc[row,1])

        grades = str(ws.iloc[row, 12])
        if currDistrict != district_name:
            currGrades = []
            currDistrict = district_name
        
        currGrades.extend(grades.split(','))
        if row < (len(ws)-1) and ws.iloc[row+1, 1].split(':')[0] == currDistrict:
            continue
        elif '09' in currGrades and '12' in currGrades:
            relevantDistricts.append(district_name)
            
'''
This method takes in the org name of a school and returns the district, school 
name, and determines if it is a public, charter, regional, or vocational school
'''
def getSchoolinfo(name):
    type = 'Public'
    district, school = name.split(':', 1)
    district = district.strip()
    district = district.replace(' (District)', '', 1)
    school = school.strip()
    
    if regionalSchools.has_key(district):
        type = 'Regional'
    
    if 'Charter' in school:
        type = 'Charter'
    
    if 'Voc' in district or 'Voc' in school:
        type = 'Vocational'
        
    return district, school, type

'''
This method checks if the passed district name exists in the school admin sheet.
If district name exists it returns True, otherwise False
'''
def districtExists(district):
    exists = False
    fileName = 'Master-School_Data-2015'
    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName+ext), sheetname='Admin-School', header=0)
    
    for row in range(len(ws)):
        if district == ws.iloc[row, 1]:
            exists = True
            break
        
    return exists

'''
This method looks through the list of regional schools for the passed in town name.
If the town is part of a regional school, the name is returned. 
If not, the passed town name is returned. 
'''
def districtLookup(town):
    district = None
    
    for k,v in regionalSchools.iteritems():
        if town in v:
            district = k
            
    return district

"""
Parse the relevant information out of the data received from the admin site
Current relevant fields are:
    Town
    School Name
    Address
    School Type
    Grades

This method will ignore no-op (not operational) schools
This method defaults to parsing data from 2015
""" 
def parseDistrictAdminData(year = "2015"):
    print "            Parsing District Admin Data"
    fileName = "admin-district-"+year
    columns = ['Town', 'School Name', 'School Type', 'School Address', 'Grades']
    rows = []
            
    """ Convert to true xls file """  
    convertToXLS(fileName, schoolDataLocation, 7, 0)

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName+ext), 0)

    for row in range(len(ws)):
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,1]:
            continue
        town = ws.iloc[row, 0].capitalize()
        school_name = ws.iloc[row, 1].replace(' (District)', '', 1)
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

"""
Parse the relevant information out of the data received from the admin site
Current relevant fields are:
    Town Name
    District Name
    School Name
    School Type (Public, Charter, Regional, Vocational)
    Zip Code
    Grades

This method defaults to parsing data from 2015
""" 
def parseSchoolAdminData(year = "2015"):
    print "            Parsing School Admin Data"
    fileName = "admin-school-"+year+ext
    columns = ['Town', 'District', 'School Name', 'School Type', 'Zip Code', 'Grades']
    rows = []
            
    """ Convert to true xls file """  
    convertToXLS(fileName, schoolDataLocation, 7, 0)

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), header=0)
    ws.sort_values(by='Org Name', inplace=True)
        
    findRelevantDistricts(ws)
     
    for row in range(len(ws)):
        town = ws.iloc[row, 0]
        district_name, school_name, school_type = getSchoolinfo(ws.iloc[row,1])
        school_code = ws.iloc[row, 2]
        function = ws.iloc[row, 4]
        contact_name = ws.iloc[row, 5]
        address1 = ws.iloc[row, 6]
        address2 = ws.iloc[row, 7]
        state = ws.iloc[row, 8]
        zipCode = '0'+str(ws.iloc[row, 9])
        contact_phone = ws.iloc[row, 10]
        contact_fax = ws.iloc[row, 11]
        grades = str(ws.iloc[row, 12])

        if district_name in relevantDistricts:
            rows.append([town, district_name, school_name, school_type, zipCode, grades])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseAccountDistrictData(year="2014"):
    print "            Parsing Accountability District Data"
    fileName = "account-district-"+year+ext
    columns = ['District', 'Level', 'Notes']
    rows = []

    """ Convert to true xls """    
    convertToXLS(fileName, schoolDataLocation, skiprows=2)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        district = ws.iloc[row, 0].replace(' (District)', '', 1)
        
        school_code = ws.iloc[row, 1]
        level = ws.iloc[row, 2]
        notes = ws.iloc[row, 3]
        num_students = ws.iloc[row, 4]
        highNeed_students = ws.iloc[row, 5]
        
        if district in relevantDistricts:
            rows.append([district, level, notes])
       
    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseAccountSchoolData(year="2014"):
    print "            Parsing Accountability School Data"
    fileName = "account-school-"+year+ext
    columns = ['Town', 'School', 'Type', 'Level', 'Notes', 'Percentile']
    rows = []

    """ Convert to true xls file """    
    convertToXLS(fileName, schoolDataLocation, skiprows=2)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        # hack because this entry has 2 ' - '
        if ws.iloc[row,0] == "Boston - ELC - West Zone":
            town = "Boston"
            school = "ELC-West Zone"
        else:
            town, school = ws.iloc[row, 0].split(' - ')
            town = town.capitalize()
            school = school.capitalize()
        
        school_code = ws.iloc[row, 1]
        level = ws.iloc[row, 2]
        notes = ws.iloc[row, 3]
        type = ws.iloc[row, 4]
        percentile = ws.iloc[row, 5]
        
        rows.append([town, school, type, level, notes, percentile])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseClassSizeDistrictData(year='2014'):
    print "            Parsing Class Size District Data"
    fileName = "class_size-district-"+year+ext
    columns = ['District', 'Avg Size', 'SPED %']
    rows = []

    """ Convert to true xls file """    
    convertToXLS(fileName, schoolDataLocation, header=0)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        district = ws.iloc[row, 0].replace(' (District)', '', 1)
        
        school_code = ws.iloc[row, 1]
        total_classes = ws.iloc[row, 2]
        avg_size = ws.iloc[row, 3]
        num_students = ws.iloc[row, 4]
        female_perc = ws.iloc[row, 5]
        male_perc = ws.iloc[row, 6]
        lep_perc = ws.iloc[row, 7]
        sped_perc = ws.iloc[row, 8]
        low_income = ws.iloc[row, 9]
        
        if district in relevantDistricts:    
            rows.append([district, avg_size, sped_perc])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseClassSizeSchoolData(year='2014'):
    print "            Parsing Class Size School Data"
    
    fileName = "class_size-school-"+year+ext
    columns = ['Town', 'School', 'Total Classes', '# Students', 'Avg Size']
    rows = []

    """ Convert to true xls file """    
    convertToXLS(fileName, schoolDataLocation, header=0)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        # hack because this entry has 2 ' - '
        if ws.iloc[row,0] == "Boston - ELC - West Zone":
            town = "Boston"
            school = "ELC-West Zone"
        else:
            town, school = ws.iloc[row, 0].split(' - ')
            town = town.capitalize()
            school = school.capitalize()
        
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
    print "            Parsing Dropout District Data"
    fileName = "dropout-district-"+year+ext
    columns = ['District', '# Enrolled', 'Total Drop', 'Total Drop %']
    rows = []

    """ Convert to true xls """    
    convertToXLS(fileName, schoolDataLocation, skiprows = 1, header=0)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        district = ws.iloc[row, 0].replace(' (District)', '', 1)
        
        school_code = ws.iloc[row, 1]
        num_enrolled = ws.iloc[row, 2]
        total_drop = ws.iloc[row, 3]
        perc_total_drop = ws.iloc[row, 4]
        perc_gr9_drop = ws.iloc[row, 5]
        perc_gr10_drop = ws.iloc[row, 6]
        perc_gr11_drop = ws.iloc[row, 7]           
        perc_gr12_drop = ws.iloc[row, 8]
             
        if district in relevantDistricts:    
            rows.append([district, num_enrolled, total_drop, perc_total_drop])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseDropoutSchoolData(year="2014"):
    print "            Parsing Dropout School Data"
    fileName = "dropout-school-"+year+ext
    columns = ['Town', 'School', '# Enrolled', 'Total Drop', 'Total Drop %']
    rows = []

    """ Convert to true xls file """    
    convertToXLS(fileName, schoolDataLocation, skiprows=1, header=0)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        # hack because this entry has 2 ' - '
        if ws.iloc[row,0] == "Boston - ELC - West Zone":
            town = "Boston"
            school = "ELC-West Zone"
        else:
            town, school = ws.iloc[row, 0].split(' - ')
            town = town.capitalize()
            school = school.capitalize()
        
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
    print "            Parsing Higher Education District Data"
    fileName = "higher_edu-district-"+year+ext
    columns = ['District', '# Grads', '# to College', '% to College']
    rows = []

    """ Convert to true xls """    
    convertToXLS(fileName, schoolDataLocation, header=0)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        district = ws.iloc[row, 0].replace(' (District)', '', 1)
        
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
            
        if district in relevantDistricts:    
            rows.append([district, num_hs_grad, num_to_coll, perc_to_coll])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseHigherEdSchoolData(year="2013"):
    print "            Parsing Higher Ed School Data"
    fileName = "higher_edu-school-"+year+ext
    columns = ['Town', 'School', '# Grads', '# to College', '% to College']
    rows = []

    """ Convert to true xls file """    
    convertToXLS(fileName, schoolDataLocation, header=0)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        # hack because this entry has 2 ' - '
        if ws.iloc[row,0] == "Boston - ELC - West Zone":
            town = "Boston"
            school = "ELC-West Zone"
        else:
            town, school = ws.iloc[row, 0].split(' - ')
            town = town.capitalize()
            school = school.capitalize()
        
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
    print "            Parsing Graduation Rates District Data"
    fileName = "grad_rates-district-"+year+ext
    columns = ['District', '# Students', '% Graduated']
    rows = []

    """ Convert to true xls """    
    convertToXLS(fileName, schoolDataLocation, header=0)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        district = ws.iloc[row, 0].replace(' (District)', '', 1)

        school_code = ws.iloc[row, 1]
        num_students = ws.iloc[row, 2]
        perc_grad = ws.iloc[row, 3]
        perc_in_school = ws.iloc[row, 4]
        perc_non_grad_complete = ws.iloc[row, 5]
        perc_ged = ws.iloc[row, 6]
        perc_dropped = ws.iloc[row, 7]           
        perc_excluded = ws.iloc[row, 8]
            
        if district in relevantDistricts:    
            rows.append([district, num_students, perc_grad])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseGraduationRateSchoolData(year="2014"):
    print "            Parsing Graduation Rates School Data"
    fileName = "grad_rates-school-"+year+ext
    columns = ['Town', 'School', '# Students', '% Grad']
    rows = []

    """ Convert to true xls file """    
    convertToXLS(fileName, schoolDataLocation, header=0)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        # hack because this entry has 2 ' - '
        if ws.iloc[row,0] == "Boston - ELC - West Zone":
            town = "Boston"
            school = "ELC-West Zone"
        else:
            town, school = ws.iloc[row, 0].split(' - ')
            town = town.capitalize()
            school = school.capitalize()
        
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
    print "            Parsing MCAS District Data"
    fileName = "mcas-district-"+year+ext
    columns = ['District', '# Students', 'Subject', '# Adv+Prof', '% Adv+Prof', '# Adv', '% Adv', '# Prof', '% Prof', '# NI', '% NI', '# W/F', '% W/F']
    rows = []

    """ Convert to true xls """    
    convertToXLS(fileName, schoolDataLocation, header=0)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        district = ws.iloc[row, 0].replace(' (District)', '', 1)
        
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
        
        if district in relevantDistricts:    
            rows.append([district, num_students, subject, num_prof_adv, perc_prof_adv, num_adv, perc_adv, num_prof, perc_prof, num_NI, perc_NI, num_WF, perc_WF])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseMCASSchoolData(year="2015"):
    print "            Parsing MCAS School Data"
    fileName = "mcas-school-"+year+ext
    columns = ['Town', 'School', '# Students', 'Subject', '# Adv', '% Adv', '# Prof', '% Prof', '# NI', '% NI', '# W/F', '% W/F' ]
    rows = []

    """ Convert to true xls file """    
    convertToXLS(fileName, schoolDataLocation, header=0)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        # hack because these entry has 2 ' - '
        if ws.iloc[row,0] == "Boston - ELC - West Zone":
            town = "Boston"
            school = "ELC-West Zone"
        elif "Easton - Richardson" in ws.iloc[row,0]:
            town = "Easton"
            school = "Olmstead School"
        else:
            town, school = ws.iloc[row, 0].split(' - ')
            town = town.capitalize()
            school = school.capitalize()
        
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
            
        rows.append([town, school, num_students, subject, num_adv, perc_adv, num_prof, perc_prof, num_NI, perc_NI, num_WF, perc_WF])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseSATDistrictData(year="2015"):
    print "            Parsing SAT District Data"
    fileName = "sat-district-"+year+ext
    columns = ['District', '# Tests', 'Reading', 'Writing', 'Math']
    rows = []

    """ Convert to true xls """    
    convertToXLS(fileName, schoolDataLocation, header=0)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        district = ws.iloc[row, 0].replace(' (District)', '', 1)

        school_code = ws.iloc[row, 1]
        tests_taken = ws.iloc[row, 2]
        reading = ws.iloc[row, 3]
        writing = ws.iloc[row, 4]
        math = ws.iloc[row, 5]
               
        if district in relevantDistricts:    
            rows.append([district, tests_taken, reading, writing, math])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseSATSchoolData(year="2015"):
    print "            Parsing SAT School Data"
    fileName = "sat-school-"+year+ext
    columns = ['Town', 'School', 'Tests Taken', 'Reading', 'Writing', 'Math']
    rows = []

    """ Convert to true xls file """    
    convertToXLS(fileName, schoolDataLocation, header=0)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):        
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        # hack because these entry has 2 ' - '
        if ws.iloc[row,0] == "Boston - ELC - West Zone":
            town = "Boston"
            school = "ELC-West Zone"
        elif "Easton - Richardson" in ws.iloc[row,0]:
            town = "Easton"
            school = "Olmstead School"
        else:
            town, school = ws.iloc[row, 0].split(' - ')
            town = town.capitalize()
            school = school.capitalize()
        
        school_code = ws.iloc[row, 1]
        tests_taken = ws.iloc[row, 2]
        reading = ws.iloc[row, 3]
        writing = ws.iloc[row, 4]
        math = ws.iloc[row, 5]
           
        rows.append([town, school, tests_taken, reading, writing, math])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseSPEDPerfData(year="2014"):
    print "            Parsing SPED Performance Data"
    fileName = "sped-performance-"+year+ext
    columns = pd.MultiIndex.from_tuples([('District', ''),
                                         ('SPED Grad Rate', 'Cohort #'), ('SPED Grad Rate', 'Grad #'), ('SPED Grad Rate', 'Grad %'), 
                                         ('SPED Dropout', 'Enrolled'), ('SPED Dropout', '# Dropped'), ('SPED Dropout', '% Dropped'),
                                         ('Ages 6-21', '# Students'), ('Ages 6-21', '# Full Incl'), ('Ages 6-21', '% Full Incl'),
                                         ('Parent Involvement', 'Period'), ('Parent Involvement', '# Meet Std'), ('Parent Involvement', '% Meet Std')
                                         ])
    rows = []

    """ Convert to true xls """    
    convertToXLS(fileName, schoolDataLocation, skiprows=2)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        district = ws.iloc[row, 0].replace(' (District)', '', 1)
        
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

        if district in relevantDistricts:    
            rows.append([district, 
                         ind1_num_cohort, ind1_num_grad, ind1_perc_grad, 
                         ind2_num_enrolled, ind2_num_dropped, ind2_perc_dropped,
                         ind6_num_students, ind6_num_full_incl, ind6_perc_full_incl,
                         ind8_period, ind8_num_meet_std, ind8_perc_meet_std])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseSPEDComplianceData(year="2014"):
    print "            Parsing SPED Compliance Data"
    fileName = "sped-compliance-"+year+ext
    columns = pd.MultiIndex.from_tuples([('District', )])
    rows = []

    """ Convert to true xls """    
    convertToXLS(fileName, schoolDataLocation, skiprows=2)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue
        district = ws.iloc[row, 0].replace(' (District)', '', 1)
                               
        if not districtExists(district):
            print 'SPED-Comp: Skipping district ', district
            continue
        
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

        if district in relevantDistricts:    
            rows.append([district])
        
    df = pd.DataFrame(rows, columns = columns)
    
    return df

def parseTeacherSalaryData(year="2013"):
    print "            Parsing Teacher Salary Data"
    fileName = "teacher-salary-"+year+ext
    columns = ['District', 'Salary Total', 'Avg Salary', 'FTE Count']
    rows = []

    """ Convert to true xls """    
    convertToXLS(fileName, schoolDataLocation, header=0)        

    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName), 0)
     
    for row in range(len(ws)):
        """ Skip Charter schools """
        if 'CHARTER' in ws.iloc[row,0]:
            continue        
        district = ws.iloc[row, 0].replace(' (District)', '', 1)
                      
        school_code = ws.iloc[row, 1]
        salary_total = ws.iloc[row, 2]
        avg_salary = ws.iloc[row, 3]
        fte_count = ws.iloc[row, 4]
               
        if district in relevantDistricts:    
            rows.append([district, salary_total, avg_salary, fte_count])

    df = pd.DataFrame(rows, columns = columns)
    
    return df

'''
This method will create a worksheet that can be used to save school ranks for 
each school. The worksheet will contain a column for each town, the school
district for that town, and a column for Rank.
The District column will contain duplicate entries for each town in that
district. 
'''
def prepSchoolTownRankData():
    
    print '            Preparing School Town Ranking Sheet'
    columns = ['Town','District','Rank']
    data = []
    currTown = ''
    currDistrict = ''
    fileName = 'Master-School_Data-2015'
    
    schoolData = pd.read_excel(os.path.join(schoolDataLocation, fileName+ext), sheetname='Admin-School', header=0)
    schoolData.sort_values(by=['District', 'Town'], inplace=True)
    
    for each in range(len(schoolData)):
        town = schoolData.iloc[each, 0]    
        district = schoolData.iloc[each, 1]
        
        if district == currDistrict:
            if town == currTown:
                continue
            else:
                currTown = town
                data.append([town, district, ''])        
        else:
            currDistrict = district
            currTown = town
            data.append([town, district, ''])    
    
    df = pd.DataFrame(data, columns = columns)
    
    return df

def prepSchoolDistrictRankData():
    print '            Preparing School District Ranking Sheet'
    columns = ['District','Rank']
    data = []
    currDistrict = ''
    fileName = 'Master-School_Data-2015'
    
    schoolData = pd.read_excel(os.path.join(schoolDataLocation, fileName+ext), sheetname='Admin-School', header=0)
    schoolData.sort_values(by=['District', 'Town'], inplace=True)
    
    for each in range(len(schoolData)):
        town = schoolData.iloc[each, 0]    
        district = schoolData.iloc[each, 1]
        
        # Skip duplicate districts
        if district == currDistrict:
                continue
        else:
            currDistrict = district
            data.append([district, ''])    
    
    df = pd.DataFrame(data, columns = columns)
    
    return df

def parseSchoolDistrictRankData():
    print '            Parsing School District Rank Data'
    
    fileName = 'school-rank-2015'
    columns = ['District', 'School Type', 'Rank', 'Grade']
    rows = []
    
    ws = pd.read_excel(os.path.join(schoolDataLocation, fileName+ext), 0)
     
    for row in range(len(ws)):
        """ Skip Charter schools """
        if 'Charter' in ws.iloc[row,0]:
            continue        
        district = ws.iloc[row, 0]
        school_type = ws.iloc[row, 1]
        district_rank = ws.iloc[row, 2]
        grade = ws.iloc[row, 3]

        if district in relevantDistricts:    
            rows.append([district, school_type, district_rank, grade])

    df = pd.DataFrame(rows, columns = columns)
    
    return df