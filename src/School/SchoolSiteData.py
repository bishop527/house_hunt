'''
Created on Nov 4, 2015

schoolDataSite objects store data about sites used to download relevant School data.
Name - common name of the data being downloaded which will be used as a reference
url - url used to download the data
currYear - the most current year of data
availYears - list of other years available for download

@author: AD23883
'''
import urllib2
 
#home_dir = "/Users/ad23883/workspace/house_hunt/"
#home_dir = "C:\\Users\\ad23883\\workspace\\house_hunt\\"
dataLocation = "data/"

class SchoolSiteData(object):

    def __init__(self, name, url, currYear, availYears):
        self.name = name
        self.url = url
        self.currYear = currYear
        self.availYears = availYears

    def getName(self):
        return self.name
    
    def getURL(self):
        return self.url
    
    def getCurrYear(self):
        return self.currYear
    
    def getAvailYears(self):
        return self.availYears
    
    def setName(self, name):
        self.name = name
        
    def setURL(self, url):
        self.url = url
    
    def setCurrYear(self, currYear):
        self.currYear = currYear
        
    def setAvailYears(self, availYears):
        self.availYears = availYears

"""
Download School specific data from all or 1 pre-defined site
Current available options are:
    admin
    account-district
    account-School
"""
def downloadSchoolData(data = 'current'):
    print "Started downloading School data"
    sites = []      
    proxy = urllib2.ProxyHandler({'http' : 'llproxy.llan.ll.mit.edu:8080'})
    opener = urllib2.build_opener(proxy)
    urllib2.install_opener(opener)
        
    sites.append(SchoolSiteData('admin', 
        'http://profiles.doe.mass.edu/search/search_export.aspx?orgCode=&orgType=5,12&runOrgSearch=Y&searchType=ORG&leftNavId=11238&showEmail=N',
        '2015', 'NA'))
    sites.append(SchoolSiteData('account-district',
        'http://profiles.doe.mass.edu/state_report/accountability.aspx?year=2014&export_excel=yes', 
        '2014', '2014,2013,2012,2011,2010,2009,2008,2007,2006,2005,2004,2003'))
    sites.append(SchoolSiteData('account-school',
        'http://profiles.doe.mass.edu/state_report/accountability.aspx?year=2014&mode=school&orderBy=&export_excel=yes',
        '2014', '2014,2013,2012,2011,2010,2009,2008,2007,2006,2005,2004,2003'))
    sites.append(SchoolSiteData('class_size-district',
        'http://profiles.doe.mass.edu/state_report/classsizebygenderpopulation.aspx?fycode=2014&export_excel=yes&subjectCode=44&reportType=DISTRICT',
        '2014', '2014,2013,2012,2011'))
    sites.append(SchoolSiteData('class_size-school',
        'http://profiles.doe.mass.edu/state_report/classsizebyraceethnicity.aspx?fycode=2014&export_excel=yes&subjectCode=44&reportType=SCHOOL',
        '2014', '2014,2013,2012,2011'))
    sites.append(SchoolSiteData('dropout-district',
        'http://profiles.doe.mass.edu/state_report/dropout.aspx?fycode=2014&export_excel=yes&reportType=DISTRICT&studentGroup=ALL',
        '2014', '2014,2013,2012,2011,2010,2009,2008'))
    sites.append(SchoolSiteData('dropout-school',
        'http://profiles.doe.mass.edu/state_report/dropout.aspx?fycode=2014&export_excel=yes&reportType=SCHOOL&studentGroup=ALL',
        '2014', '2014,2013,2012,2011,2010,2009,2008'))
    sites.append(SchoolSiteData('higher_edu-district',
        'http://profiles.doe.mass.edu/state_report/gradsattendingcollege.aspx?fycode=2013&export_excel=yes&stateGroup=ALL&reportType=DISTRICT&studentGroup=ALL',
        '2013', '2013,2012,2011,2010,2009,2008,2007,2006,2005,2004'))
    sites.append(SchoolSiteData('higher_edu-school',
        'http://profiles.doe.mass.edu/state_report/gradsattendingcollege.aspx?fycode=2013&export_excel=yes&stateGroup=ALL&reportType=SCHOOL&studentGroup=ALL',
        '2013', '2013,2012,2011,2010,2009,2008,2007,2006,2005,2004'))
    sites.append(SchoolSiteData('grad_rates-district',
        'http://profiles.doe.mass.edu/state_report/gradrates.aspx?&export_excel=yes&cohortYear=2014&reportType=DISTRICT&rateType=4-Year:REG&studentGroup=5',
        '2014', '2014,2013,2012,2011,2010,2009,2008,2007,2006'))        
    sites.append(SchoolSiteData('grad_rates-school',
        'http://profiles.doe.mass.edu/state_report/gradrates.aspx?&export_excel=yes&cohortYear=2014&reportType=SCHOOL&rateType=4-Year:REG&studentGroup=5',
        '2014', '2014,2013,2012,2011,2010,2009,2008,2007,2006'))
    sites.append(SchoolSiteData('mcas-district',
        'http://profiles.doe.mass.edu/state_report/mcas.aspx?&export_excel=yes&ctl00$ContentPlaceHolder1$reportType=DISTRICT&ctl00$ContentPlaceHolder1$grade=AL&apply2006=Y&ctl00$ContentPlaceHolder1$year=2015&ctl00$ContentPlaceHolder1$studentGroup=AL:AL&ctl00$ContentPlaceHolder1$SchoolType=All',
        '2015', '2015,2014,2013,2012,2011,2010,2009,2008,2007,2006,2005,2004,2003,2002,2001,2000,1999,1998'))
    sites.append(SchoolSiteData('mcas-school',
        'http://profiles.doe.mass.edu/state_report/mcas.aspx?&export_excel=yes&ctl00$ContentPlaceHolder1$reportType=SCHOOL&ctl00$ContentPlaceHolder1$grade=AL&apply2006=Y&ctl00$ContentPlaceHolder1$year=2015&ctl00$ContentPlaceHolder1$studentGroup=AL:AL&ctl00$ContentPlaceHolder1$SchoolType=All',
        '2015', '2015,2014,2013,2012,2011,2010,2009,2008,2007,2006,2005,2004,2003,2002,2001,2000,1999,1998'))
    sites.append(SchoolSiteData('sat-district',
        'http://profiles.doe.mass.edu/state_report/sat_perf.aspx?fycode=2015&export_excel=yes&reportType=DISTRICT&studentGroup=ALL',
        '2015', '2015,2014,2013,2012,2011,2010,2009,2008,2007,2006,2005'))
    sites.append(SchoolSiteData('sat-school',
        'http://profiles.doe.mass.edu/state_report/sat_perf.aspx?fycode=2015&export_excel=yes&reportType=SCHOOL&studentGroup=ALL',
        '2015', '2015,2014,2013,2012,2011,2010,2009,2008,2007,2006,2005'))
    sites.append(SchoolSiteData('sped-performance',
        'http://profiles.doe.mass.edu/state_report/special_ed.aspx?&export_excel=yes&year=2014&IndicatorType=Performance',
        '2014', '2014,2013,2012,2011,2010,2009,2008,2007,2006'))
    sites.append(SchoolSiteData('sped-compliance',
        'http://profiles.doe.mass.edu/state_report/special_ed.aspx?&export_excel=yes&year=2014&IndicatorType=Compliance',
        '2014', '2014,2013,2012,2011,2010,2009,2008,2007,2006'))        
    sites.append(SchoolSiteData('teacher-salary',
        'http://profiles.doe.mass.edu/state_report/teachersalaries.aspx?mode=&orderBy=&year=2013&filterBy=&export_excel=yes',
        '2013', '2013,2012,2011,2010,2009,2008,2007,2006,2005,2004,2003,2002,2001,2000,1999,1998,1997'))     
    
    if data == 'current':
        for site in sites:
            name = site.getName()
            url = site.getURL()
            currYear = site.getCurrYear()
            
            with open(dataLocation+name+'-'+currYear+'.xlsx', 'wb') as f:
                f.write(urllib2.urlopen(url).read())
                f.close()