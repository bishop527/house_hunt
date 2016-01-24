'''
Created on Nov 16, 2015

@author: ad23883
@todo: 
'''
from utils import *
import googlemaps
from House.HouseData import getMATowns

def getCommuteData():    
    print '        Downloading Commute Data'
    googleAPIkey = 'AIzaSyDtNP2h8YzQzUdWJ_2JvspP4nAJhg7m9LQ'
    if proxy_on:
        gmaps = googlemaps.Client(key=googleAPIkey, requests_kwargs={'proxies':{'https':'http://llproxy.llan.ll.mit.edu:8080'}})
    else:
        gmaps = googlemaps.Client(key=googleAPIkey)
        
    destination = '244 Wood St. Lexington, MA'
    mode = 'driving'
    language = 'en'
    avoid = 'tolls'
    units = 'imperial'
    # seconds from 1 Jan 1970 to 2 May 2016 07:00 EST
    departure_time = DEPARTURE_TIME
    traffic_model = TRAFFIC_MODEL
    
    towns = getMATowns()
    origins = ''
    
    """ Need to seperate list of towns into chunks of 100 """
    for each in towns[:100]:
        origins += each+', MA|'
    origins = origins[:-1]
     
    commuteData1 = gmaps.distance_matrix(origins, destination, mode=mode, language=language, avoid=avoid, 
                                         units=units, departure_time=departure_time, traffic_model=traffic_model)
     
    origins = ''
    for each in towns[100:200]:
        origins += each+', MA|'
    origins = origins[:-1]
      
    commuteData2 = gmaps.distance_matrix(origins, destination, mode=mode, language=language, avoid=avoid, 
                                         units=units, departure_time=departure_time, traffic_model=traffic_model)
     
    origins = ''
    for each in towns[200:300]:
        origins += each+', MA|'
    origins = origins[:-1]
      
    commuteData3 = gmaps.distance_matrix(origins, destination, mode=mode, language=language, avoid=avoid, 
                                         units=units, departure_time=departure_time, traffic_model=traffic_model)
     
    origins = ''
    for each in towns[300:]:
        origins += each+', MA|'
    origins = origins[:-1]
      
    commuteData4 = gmaps.distance_matrix(origins, destination, mode=mode, language=language, avoid=avoid, 
                                         units=units, departure_time=departure_time, traffic_model=traffic_model)
     
    return commuteData1, commuteData2, commuteData3, commuteData4
