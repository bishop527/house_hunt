'''
Created on Nov 16, 2015
Updated on Dec 30, 2025

@author: ad23883
'''

import googlemaps
from utils import *
from constants import *
from datetime import datetime

def get_commute_data(origins, departure_time, destination):
    # Get Google API Key
    api_key = get_google_api_key()

    print('        Downloading Commute Data')
    if PROXY_ON:
        gmaps = googlemaps.Client(key=api_key, requests_kwargs={'proxies':{'https':'http://localhost:8080'}})
    else:
        gmaps = googlemaps.Client(key=api_key)

    mode = 'driving'
    language = 'en'
    units = 'imperial'

    commute_data = []

    # Loop through the list 25 items at a time
    for i in range(0, len(destination), CHUNK_SIZE):
        # Create the chunk
        chunk = destination[i: i + CHUNK_SIZE]

        print(f"Requesting chunk: {i} to {i + len(chunk)} of {len(destination)}")

        try:
            # Single API call for 25 destinations
            response = gmaps.distance_matrix(
                origins=origins,
                destinations=chunk,
                mode='driving',
                departure_time=datetime.now()
            )

            # Extract the 'elements' for this specific chunk
            elements = response['rows'][0]['elements']

            # Consolidate results with the address names
            for index, element in enumerate(elements):
                if element['status'] == 'OK':
                    commute_data.append({
                        'destination': chunk[index],
                        'distance': element['distance']['text'],
                        'duration': element['duration']['text'],
                        'duration_in_traffic': element.get('duration_in_traffic', {}).get('text', 'N/A'),
                        'seconds': element['duration']['value']  # Useful for sorting
                    })
                else:
                    commute_data.append({
                        'destination': chunk[index],
                        'status': element['status']
                    })

        except Exception as e:
            print(f"API Error at index {i}: {e}")

    return commute_data
