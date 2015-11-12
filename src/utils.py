'''
Created on Nov 4, 2015

@author: AD23883
'''
import pandas as pd
import platform
import pwd
import urllib2
import openpyxl as pyxl
import os.path

""" 
Appends the given DataFrame with the master workbook and names the worksheet the given sheetName 
"""
def populateMaster(fileName, df):
    for sheetName, data in df.iteritems():
        print "Adding", sheetName, "to", fileName
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

def getMATowns():
    towns = ['Abington','Acton','Acushnet','Adams','Agawam','Alford','Amesbury','Amherst','Andover','Aquinnah','Arlington','Ashburnham','Ashby','Ashfield','Ashland','Athol','Attleboro','Auburn','Avon','Ayer',
    'Barnstable','Barre','Becket','Bedford','Belchertown','Bellingham','Belmont','Berkley','Berlin','Bernardston','Beverly','Billerica','Blackstone','Blandford','Bolton','Boston','Bourne','Boxborough','Boxford','Boylston','Braintree','Brewster','Bridgewater','Brighton','Brimfield','Brockton','Brookfield','Brookline','Buckland','Burlington',
    'Cambridge','Canton','Carlisle','Carver','Charlemont','Charlestown','Charlton','Chatham','Chelmsford','Chelsea','Cheshire','Chester','Chesterfield','Chicopee','Chilmark','Clarksburg','Clinton','Cohasset','Colrain','Concord','Conway','Cummington',
    'Dalton','Dana','Danvers','Dartmouth','Dedham','Deerfield','Dennis','Dighton','Douglas','Dorchester','Dover','Dracut','Dudley','Dunstable','Duxbury',
    'East Bridgewater','East Brookfield','East Longmeadow','Eastham','Easthampton','Easton','Edgartown','Egremont','Enfield','Erving','Essex','Everett',
    'Fairhaven','Fall River','Falmouth','Fitchburg','Florida','Foxborough','Framingham','Franklin','Freetown',
    'Gardner','Georgetown','Gill','Gloucester','Goshen','Grafton','Granby','Granville','Great Barrington','Greenfield','Greenwich','Groton','Groveland',
    'Hadley','Halifax','Hamilton','Hampden','Hancock','Hanover','Hanson','Hardwick','Harvard','Harwich','Hatfield','Haverhill','Hawley','Heath','Hingham','Hinsdale','Holbrook','Holden','Holland','Holliston','Holyoke','Hopedale','Hopkinton','Hubbardston','Hudson','Hull','Huntington','Hyde Park',
    'Ipswich','Kingston',
    'Lakeville','Lancaster','Lanesborough','Lawrence','Lee','Leicester','Lenox','Leominster','Leverett','Lexington','Leyden','Lincoln','Littleton','Longmeadow','Lowell','Ludlow','Lunenburg','Lynn','Lynnfield',
    'Malden','Manchester-By-The-Sea','Mansfield','Marblehead','Marion','Marlborough','Marshfield','Mashpee','Mattapoisett','Maynard','Medfield','Medford','Medway','Melrose','Mendon','Merrimac','Methuen','Middleborough','Middlefield','Middleton','Milford','Millbury','Millis','Millville','Milton','Monroe','Monson','Montague','Monterey','Montgomery','Mount Washington',
    'Nahant','Nantucket','Natick','Needham','New Ashford','New Bedford','New Braintree','New Marlborough','New Salem','Newbury','Newburyport','Newton','Norfolk','North Adams','North Andover','North Attleborough','North Brookfield','North Reading','Northampton','Northborough','Northbridge','Northfield','Norton','Norwell','Norwood',
    'Oak Bluffs','Oakham','Orange','Orleans','Otis','Oxford',
    'Palmer','Paxton','Peabody','Pelham','Pembroke','Pepperell','Peru','Petersham','Phillipston','Pittsfield','Plainfield','Plainville','Plymouth','Plympton','Prescott','Princeton','Provincetown',
    'Quincy','Randolph','Raynham','Reading','Rehoboth','Revere','Richmond','Rochester','Rockland','Rockport','Rowe','Rowley','Roxbury','Royalston','Russell','Rutland',
    'Salem','Salisbury','Sandisfield','Sandwich','Saugus','Savoy','Scituate','Seekonk','Sharon','Sheffield','Shelburne','Sherborn','Shirley','Shrewsbury','Shutesbury','Somerset','Somerville','South Hadley','Southampton','Southborough','Southbridge','Southwick','Spencer','Springfield','Sterling','Stockbridge','Stoneham','Stoughton','Stow','Sturbridge','Sudbury','Sunderland','Sutton','Swampscott','Swansea',
    'Taunton','Templeton','Tewksbury','Tisbury','Tolland','Topsfield','Townsend','Truro','Tyngsborough','Tyringham',
    'Upton','Uxbridge','Wakefield','Wales','Walpole','Waltham','Ware','Wareham','Warren','Warwick','Washington','Watertown','Wayland','Webster','Wellesley','Wellfleet','Wendell','Wenham','West Boylston','West Bridgewater','West Brookfield','West Newbury','West Roxbury','West Springfield','West Stockbridge','West Tisbury','Westborough','Westfield','Westford','Westhampton','Westminster','Weston','Westport','Westwood','Weymouth','Whately','Whitman','Wilbraham','Williamsburg','Williamstown','Wilmington','Winchendon','Winchester','Windsor','Winthrop','Woburn','Worcester','Worthington','Wrentham','Yarmouth']
    
    return towns
        