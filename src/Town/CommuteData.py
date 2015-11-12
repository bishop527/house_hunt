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
    for each in towns[:25]:
        origins += each+', MA|'
    origins = origins[:-1]
    
    commuteData1 = gmaps.distance_matrix(origins, destination, mode=mode, language=language, avoid=avoid, units=units)
    
    origins = ''
    for each in towns[25:50]:
        origins += each+', MA|'
    origins = origins[:-1]
    
    commuteData2 = gmaps.distance_matrix(origins, destination, mode=mode, language=language, avoid=avoid, units=units)
    
    return commuteData1, commuteData2