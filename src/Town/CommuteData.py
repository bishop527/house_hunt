'''
Created on Nov 9, 2015

@author: ad23883
'''
import utils
import googlemaps

dataLocation = 'data/town/'

def getCommuateData():
    
    googleAPIkey = 'AIzaSyDtNP2h8YzQzUdWJ_2JvspP4nAJhg7m9LQ'
    gmaps = googlemaps.Client(key=googleAPIkey)
    destination = '244 Wood St. Lexington, MA'
    mode = 'driving'
    language = 'en'
    avoid = 'tolls'
    units = 'imperial'
    
    towns = utils.getMATowns()
    origins = ''
    
    """ Need to seperate list of towns into chunks of 100 """
    for each in towns[:105]:
        origins += each+', MA|'
    origins = origins[:-1]
    
    commuteData = gmaps.distance_matrix(origins, destination, mode=mode, language=language, avoid=avoid, units=units)
#     origins = ''
#     for each in towns[:100]:
#         origins += each+', MA|'
#     origins = origins[:-1]
    
    return commuteData