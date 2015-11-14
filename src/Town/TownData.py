'''
Created on Nov 9, 2015

@author: ad23883
'''
import utils
import googlemaps
import pandas as pd

dataLocation = 'data/town/'

def getCommuateData():    
    googleAPIkey = 'AIzaSyDtNP2h8YzQzUdWJ_2JvspP4nAJhg7m9LQ'
    #gmaps = googlemaps.Client(key=googleAPIkey, requests_kwargs={'proxies':{'https':'http://llproxy.llan.ll.mit.edu:8080'}})
    gmaps = googlemaps.Client(key=googleAPIkey)
    destination = '244 Wood St. Lexington, MA'
    mode = 'driving'
    language = 'en'
    avoid = 'tolls'
    units = 'imperial'
    
    towns = utils.getMATowns()
    origins = ''
    
    """ Need to seperate list of towns into chunks of 100 """
    for each in towns[:100]:
        origins += each+', MA|'
    origins = origins[:-1]
    
#     """ alternate method using url """
#     url_base = 'https://maps.googleapis.com/maps/api/distancematrix/xml?key'
#     query_args = {
#                   'origins': origins,
#                   'destinations': destination,
#                   'mode': mode,
#                   'language': language,
#                   'avoid': avoid,
#                   'units': units,
#                   'key':googleAPIkey
#                   }
     
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


