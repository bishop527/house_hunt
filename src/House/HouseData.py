'''
Created on Nov 9, 2015

@author: ad23883
@todo: 
'''
import pandas as pd
import os

dataLocation = 'data/house/'
ext = '.xlsx'

def getMATowns():
    towns = ['Abington','Acton','Acushnet','Adams','Agawam','Alford','Amesbury','Amherst','Andover','Arlington','Ashburnham','Ashby','Ashfield','Ashland','Athol','Attleboro','Auburn','Avon','Ayer',
    'Barnstable','Barre','Becket','Bedford','Belchertown','Bellingham','Belmont','Berkley','Berlin','Bernardston','Beverly','Billerica','Blackstone','Blandford','Bolton','Boston','Bourne','Boxborough','Boxford','Boylston','Braintree','Brewster','Bridgewater','Brimfield','Brockton','Brookfield','Brookline','Buckland','Burlington',
    'Cambridge','Canton','Carlisle','Carver','Charlemont','Charlton','Chatham','Chelmsford','Chelsea','Cheshire','Chester','Chesterfield','Chicopee','Chilmark','Clarksburg','Clinton','Cohasset','Colrain','Concord','Conway','Cummington',
    'Dalton','Danvers','Dartmouth','Dedham','Deerfield','Dennis','Dighton','Douglas','Dorchester','Dover','Dracut','Dudley','Dunstable','Duxbury',
    'East Bridgewater','East Brookfield','East Longmeadow','Eastham','Easthampton','Easton','Edgartown','Egremont','Enfield','Erving','Essex','Everett',
    'Fairhaven','Fall River','Falmouth','Fitchburg','Florida','Foxborough','Framingham','Franklin','Freetown',
    'Gardner','Georgetown','Gill','Gloucester','Goshen','Grafton','Granby','Granville','Great Barrington','Greenfield','Groton','Groveland',
    'Hadley','Halifax','Hamilton','Hampden','Hancock','Hanover','Hanson','Hardwick','Harvard','Harwich','Hatfield','Haverhill','Hawley','Heath','Hingham','Hinsdale','Holbrook','Holden','Holland','Holliston','Holyoke','Hopedale','Hopkinton','Hubbardston','Hudson','Hull','Huntington','Hyde Park',
    'Ipswich','Kingston',
    'Lakeville','Lancaster','Lanesborough','Lawrence','Lee','Leicester','Lenox','Leominster','Leverett','Lexington','Leyden','Lincoln','Littleton','Longmeadow','Lowell','Ludlow','Lunenburg','Lynn','Lynnfield',
    'Malden','Manchester-By-The-Sea','Mansfield','Marblehead','Marion','Marlborough','Marshfield','Mashpee','Mattapoisett','Maynard','Medfield','Medford','Medway','Melrose','Mendon','Merrimac','Methuen','Middleborough','Middlefield','Middleton','Milford','Millbury','Millis','Millville','Milton','Monroe','Monson','Montague','Monterey','Montgomery','Mount Washington',
    'Nahant','Nantucket','Natick','Needham','New Ashford','New Bedford','New Braintree','New Marlborough','New Salem','Newbury','Newburyport','Newton','Norfolk','North Adams','North Andover','North Attleborough','North Brookfield','North Reading','Northampton','Northborough','Northbridge','Northfield','Norton','Norwell','Norwood',
    'Oak Bluffs','Oakham','Orange','Orleans','Otis','Oxford',
    'Palmer','Paxton','Peabody','Pelham','Pembroke','Pepperell','Peru','Petersham','Phillipston','Pittsfield','Plainfield','Plainville','Plymouth','Plympton','Princeton','Provincetown',
    'Quincy','Randolph','Raynham','Reading','Rehoboth','Revere','Richmond','Rochester','Rockland','Rockport','Rowe','Rowley','Royalston','Russell','Rutland',
    'Salem','Salisbury','Sandisfield','Sandwich','Saugus','Savoy','Scituate','Seekonk','Sharon','Sheffield','Shelburne','Sherborn','Shirley','Shrewsbury','Shutesbury','Somerset','Somerville','South Hadley','Southampton','Southborough','Southbridge','Southwick','Spencer','Springfield','Sterling','Stockbridge','Stoneham','Stoughton','Stow','Sturbridge','Sudbury','Sunderland','Sutton','Swampscott','Swansea',
    'Taunton','Templeton','Tewksbury','Tisbury','Tolland','Topsfield','Townsend','Truro','Tyngsborough','Tyringham',
    'Upton','Uxbridge','Wakefield','Wales','Walpole','Waltham','Ware','Wareham','Warren','Warwick','Washington','Watertown','Wayland','Webster','Wellesley','Wellfleet','Wendell','Wenham','West Boylston','West Bridgewater','West Brookfield','West Newbury','West Springfield','West Stockbridge','Westborough','Westfield','Westford','Westhampton','Westminster','Weston','Westport','Westwood','Weymouth','Whately','Whitman','Wilbraham','Williamsburg','Williamstown','Wilmington','Winchendon','Winchester','Windsor','Winthrop','Woburn','Worcester','Worthington','Wrentham','Yarmouth']
    
    return towns

'''
Parses out and returns zip codes from town_zips.xlsx
'''
def getMAZips():
    fileName = 'town_zips'
    zips = []

    data = pd.read_excel(dataLocation+fileName+ext, header=0)
    
    for zipCode in data.Zip:
        # Leading zero is stripped so need to re-add
        zips.append('0'+str(zipCode))
        
    return zips
'''
This method looks for the passed zip in the Town_Admin sheet. 
If it exists then return the associated town name. If not return None
'''
def zipLookup(zip):
    town = None
    fileName = 'Town_Admin-2015'
    
    townData = pd.read_excel(dataLocation+fileName+ext)
    
    for row in range(len(townData)):
        zips = (townData.iloc[row][1].split(','))
        zips = zips[:-1]
        if zip in zips:
            town = townData.iloc[row][0]
    
    return town

def townExists(town):
    exists = False
    
    allTowns = getMATowns()
    if town in allTowns:
        exists = True
        
    return exists
    
def taxRateLookup(town):
    taxRate = None
    fileName = 'TownTaxRates-2015'
    taxData = pd.read_excel(dataLocation+fileName+ext)
    
    for row in range(len(taxData)):
        if taxData.iloc[row][1] == town:
            taxRate = taxData.iloc[row][3]
    
    return taxRate

def countyLookup(zip):
    county = None
    fileName = 'Town_Admin-2015'
    
    townData = pd.read_excel(dataLocation+fileName+ext)
    
    for row in range(len(townData)):
        zips = (townData.iloc[row][1].split(','))
        zips = zips[:-1]
        if zip in zips:
            county = townData.iloc[row][2]
    
    return county
