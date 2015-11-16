'''
Created on Nov 9, 2015

@author: ad23883
'''
import utils
import googlemaps
import pandas as pd
import os
from ParseTownData import parseTownAdminData
import urllib2

dataLocation = 'data/town/'
ext = 'xlsx'

def getCommuateData():    
    print 'Downloading Commute Data'
    googleAPIkey = 'AIzaSyDtNP2h8YzQzUdWJ_2JvspP4nAJhg7m9LQ'
    gmaps = googlemaps.Client(key=googleAPIkey, requests_kwargs={'proxies':{'https':'http://llproxy.llan.ll.mit.edu:8080'}})
    #gmaps = googlemaps.Client(key=googleAPIkey)
    destination = '244 Wood St. Lexington, MA'
    mode = 'driving'
    language = 'en'
    avoid = 'tolls'
    units = 'imperial'
    
    towns = getMATowns()
    origins = ''
    
    """ Need to seperate list of towns into chunks of 100 """
    for each in towns[:100]:
        origins += each+', MA|'
    origins = origins[:-1]
     
    commuteData1 = gmaps.distance_matrix(origins, destination, mode=mode, language=language, avoid=avoid, units=units)
     
    origins = ''
    for each in towns[100:200]:
        origins += each+', MA|'
    origins = origins[:-1]
     
    commuteData2 = gmaps.distance_matrix(origins, destination, mode=mode, language=language, avoid=avoid, units=units)
    
    origins = ''
    for each in towns[200:300]:
        origins += each+', MA|'
    origins = origins[:-1]
     
    commuteData3 = gmaps.distance_matrix(origins, destination, mode=mode, language=language, avoid=avoid, units=units)
    
    origins = ''
    for each in towns[300:]:
        origins += each+', MA|'
    origins = origins[:-1]
     
    commuteData4 = gmaps.distance_matrix(origins, destination, mode=mode, language=language, avoid=avoid, units=units)
    
    return commuteData1, commuteData2, commuteData3, commuteData4

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

'''
Parses out and returns zip codes from town_zips.xlsx
'''
def getMAZips():
    fileName = 'town_zips.xlsx'
    zips = []

    data = pd.read_excel(dataLocation+fileName, header=0)
    
    for zipCode in data.Zip:
        # Leading zero is stripped so need to re-add
        zips.append('0'+str(zipCode))
        
    return zips

def townLookup(zip):
    town = None
    
    # Check if Town_Admin-2015.xlsx exists
    if not os.path.isfile(dataLocation+'Town_Admin-2015.xlsx'):
        parseTownAdminData()
    
    townData = pd.read_excel(dataLocation+'Town_Admin-2015.xlsx')
    
    for row in range(len(townData)):
        zips = (townData.iloc[row][1].split(','))
        zips = zips[:-1]
        if zip in zips:
            town = townData.iloc[row][0]
    
    return town

def taxRateLookup(town):
    taxRate = None

    taxData = pd.read_excel(dataLocation+'TownTaxRates-2015.xlsx')
    
    for row in range(len(taxData)):
        if taxData.iloc[row][1] == town:
            taxRate = taxData.iloc[row][3]
    
    return taxRate

def countyLookup(zip):
    county = None
    
    # Check if Town_Admin-2015.xlsx exists
    if not os.path.isfile(dataLocation+'Town_Admin-2015.xlsx'):
        parseTownAdminData()
    
    townData = pd.read_excel(dataLocation+'Town_Admin-2015.xlsx')
    
    for row in range(len(townData)):
        zips = (townData.iloc[row][1].split(','))
        zips = zips[:-1]
        if zip in zips:
            county = townData.iloc[row][2]
    
    return county
