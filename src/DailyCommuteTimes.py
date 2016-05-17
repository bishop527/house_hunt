'''
Created on Apr 9, 2016
@author: Adrian

The purpose of this method is to calculate commute times of a given origin and 
destination during a given time range.

1. Give an origin and destination
2. Give a time range
3. Get current system time
4. If current system time is within the time range calculate commute time of origin and destination

'''
from utils import *
import os.path
import datetime
import time
from Commute.CommuteData import getCommuteData
from Commute.ParseCommuteData import parseCommuteData
from collections import OrderedDict

frames = []
entries = OrderedDict()
data = OrderedDict()

towns = 'Somerset, MA| Franklin, MA| Medway, MA'
work = '244 Wood St. Lexington, MA'
fileName = "Daily-Commute-Times"

columns = ['Date', 'Day', 'Time', ]
weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

morningTimes = ['6:30', '6:45', '7:00', '7:15', '7:30']
afternoonTimes = ['16:30', '16:45', '17:00', '17:15', '17:30', '17:45', '18:00']

total = 0
count = 0

for each in towns.split('|'):
    town = each.split(',')[0].strip()
    data[town] = OrderedDict()
    
    data[town].update({'date': 0, 'day': 0, 'times': OrderedDict()})
    for t in morningTimes:
        data[town]['times'].update({t: {'dist':0, 'dur':0}})
    
    for t in afternoonTimes:
        data[town]['times'].update({t: {'dist':0, 'dur':0}})
        
    data[town].update({'max':0, 'min': 999, 'total': 0})
        
# Mon = 0, Sun = 6
currDay = datetime.datetime.today().weekday()  

print 'Started Processing Daily Commute'
while True:
    # Check if today is between Monday and Friday
    if currDay < 5:
        weekDay = weekDays[currDay]
        today = str(datetime.date.today())    
        x = 0
              
        currHour = str(datetime.datetime.now().hour)
        currMin = datetime.datetime.now().minute
        # Add a leading 0 when minutes is < 10
        if currMin < 10:
            currMin = '0'+str(currMin)
        else:
            currMin = str(currMin)
# 
#         # Add a leading 0 when hours is < 10
#         if currHour < 10:
#             currHour = '0'+str(currHour)
#         else:
#             currHour = str(currHour)
            
        currTime = currHour+':'+currMin
        
        if currTime in morningTimes or currTime in afternoonTimes: 
            print 'Processing for time ', currTime
            date = str(datetime.datetime.now().date())
            if currTime in morningTimes:
                commuteData = getCommuteData(towns, 'now', work)
                for row in range(len(commuteData["rows"])):
                    origin = str(commuteData['origin_addresses'][row]).split(',')[0]
                    destination = commuteData['destination_addresses'][0]
                    duration = convertToMin(str(commuteData['rows'][row]['elements'][0]['duration']['text']))
                    duration_in_traffic = convertToMin(str(commuteData['rows'][row]['elements'][0]['duration_in_traffic']['text']))
                    distance = str(commuteData['rows'][row]['elements'][0]['distance']['text']).split(' ')[0]
                
                    data[origin]['date'] = date
                    data[origin]['day'] = weekDay
                    data[origin]['times'][currTime]['dur'] = duration_in_traffic
                    data[origin]['times'][currTime]['dist'] = distance

                    if duration_in_traffic > data[origin]['max']:
                        data[origin]['max'] = duration_in_traffic
                    if duration_in_traffic < data[origin]['min']:
                        data[origin]['min'] = duration_in_traffic
                        data[origin]['total'] = data[origin]['total'] + duration_in_traffic
            else:
                commuteData = getCommuteData(work, 'now', towns)
                
                for row in range(len(commuteData["destination_addresses"])):
                    origin = commuteData['origin_addresses'][0]
                    destination = str(commuteData['destination_addresses'][row]).split(',')[0]
                    duration = convertToMin(str(commuteData['rows'][0]['elements'][row]['duration']['text']))
                    duration_in_traffic = convertToMin(str(commuteData['rows'][0]['elements'][row]['duration_in_traffic']['text']))
                    distance = str(commuteData['rows'][0]['elements'][row]['distance']['text']).split(' ')[0]
                    
                    data[destination]['date'] = date
                    data[destination]['day'] = weekDay
                    data[destination]['times'][currTime]['dur'] = duration_in_traffic
                    data[destination]['times'][currTime]['dist'] = distance
    
                    if duration_in_traffic > data[destination]['max']:
                        data[destination]['max'] = duration_in_traffic
                    if duration_in_traffic < data[destination]['min']:
                        data[destination]['min'] = duration_in_traffic
                    data[destination]['total'] = data[destination]['total'] + duration_in_traffic
                    
            # if the last afternoon time, write results for the day
            if currTime == afternoonTimes[-1]:
                writeData = [[]]
                for town in data:
                    writeData[0] = [date, weekDay]
                    currDf = pd.read_excel(os.path.join(commuteDataLocation, fileName+ext), index_col=0, sheetname=town, engine='xlrd')
                    col = currDf.columns
                    for t in data[town]['times']:
                        writeData[0].append(data[town]['times'][t]['dist'])
                        writeData[0].append(data[town]['times'][t]['dur'])
                        if data[town]['times'][t]['dur'] > 0: count += 1
                    
                    writeData[0].append(data[town]['max'])
                    writeData[0].append(data[town]['min'])
                    writeData[0].append(data[town]['total']/count)
                    newDf = pd.DataFrame(writeData, columns=col)
                    frames.append(currDf)
                    frames.append(newDf)
                    entries[town] = pd.concat(frames)
                    frames = []
                    count = 0
                    total = 0
    
                populateMaster(os.path.join(commuteDataLocation, fileName+ext), entries)
                print 'Wrote data for the day to file'
                time.sleep(3600)
                
            print 'Done processing for time ', currTime
            time.sleep(60)
        else:
            time.sleep(60)
    else:
        print 'Today is not a weekday'
        time.sleep(3600)






