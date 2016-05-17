'''
Created on Nov 16, 2015

@author: ad23883
@todo: 
'''
from utils import *
import googlemaps

def getCommuteData(origins, departure_time = DEPARTURE_TIME, destination = DESTINATION):    
    print '        Downloading Commute Data'
    googleAPIkey = 'AIzaSyDtNP2h8YzQzUdWJ_2JvspP4nAJhg7m9LQ'
    if proxy_on:
        gmaps = googlemaps.Client(key=googleAPIkey, requests_kwargs={'proxies':{'https':'http://llproxy.llan.ll.mit.edu:8080'}})
    else:
        gmaps = googlemaps.Client(key=googleAPIkey)
    
    mode = 'driving'
    language = 'en'
    units = 'imperial'
    
    traffic_model = TRAFFIC_MODEL
        
    commuteData = gmaps.distance_matrix(origins, destination, mode=mode, language=language, avoid=AVOID_TOLLS, 
                                         units=units, departure_time=departure_time, traffic_model=traffic_model)
     
     
    return commuteData
