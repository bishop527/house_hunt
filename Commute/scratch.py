import holidays
import time
from datetime import datetime
import googlemaps
from collections import OrderedDict
from Commute.CommuteData import *
from utils import *
from constants import *


'''
Take in town_data as a list of addresses that is in a format suitable for API Distance Matrix
    e.g. Somerset, MA 02726
Get commute times
Combine town Data and commute times
'''
def get_daily_commute_time(town_data):
    file_name = "Daily-Commute-Times.xlsx"
    entries = OrderedDict()

    # Mon = 0, Sun = 6
    curr_day = datetime.datetime.today().weekday()

    test_time = datetime.datetime.now().strftime("%H:%M")
    commute_times = [test_time]
    data = OrderedDict()

    columns = ['Date', 'Day', 'Time', ]
    week_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    morning_times = ['6:30', '7:00', '7:30']
    afternoon_times = ['17:00', '17:30', '18:00']
    total = 0
    count = 0

    addresses = list()
    for index, row in town_data.iterrows():
        town = row["Town"]
        state = row["State"]
        zip_code = row["Zip"]

        # Put town Data in correct format for API distance matrix
        address = town + " " + state + ", " + zip_code
        addresses.append(address)

        # Create Data structure of Towns, Zips, commute times
        if state not in data:
            data[state] = OrderedDict()

        if town not in data[state]:
            data[state][town] = OrderedDict()

        data[state][town][zip_code] = {'date': 0, 'day': 0, 'times': OrderedDict()}

        for t in commute_times:
            data[state][town][zip_code]['times'].update({t: {'dist': 0, 'dur': 0}})

        data[state][town][zip_code].update({'max': 0, 'min': 999, 'total': 0})

    print('Started Processing Daily Commute')

    while True:
        # Check if today is between Monday and Friday
        if curr_day < 5:
            now = datetime.datetime.now()
            date = now.date()
            noon_time = now.replace(hour=12, minute=0, second=0, microsecond=0).strftime("%H:%M")
            week_day = now.strftime("%A")
            curr_time = now.strftime("%H:%M")

            if curr_time in commute_times:
                count = -1
                print('Processing for time ', curr_time)

                if curr_time < noon_time:
                    commute_data = get_commute_data(addresses, 'now', WORK_ADDR)
                else:
                    commute_data = get_commute_data(WORK_ADDR, 'now', addresses)

                for batch in commute_data:
                    for row in range(len(batch["rows"])):
                        count += 1
                        town = batch['origin_addresses'][row].split(',')[0]
                        # print(count, " Working on", town)
                        state_zip = batch['origin_addresses'][row].split(', ')[1]
                        state = state_zip.split(' ')[0]
                        if 2 > len(state_zip.split(' ')):
                            zip_code = addresses[count].split(', ')[1]
                            print("No zip for", addresses[count])
                        else:
                            zip_code = state_zip.split(' ')[1]

                        destination = batch['destination_addresses'][0]
                        duration = convertToMin(str(batch['rows'][row]['elements'][0]['duration']['text']))
                        duration_in_traffic = convertToMin(
                            str(batch['rows'][row]['elements'][0]['duration_in_traffic']['text']))
                        distance = str(batch['rows'][row]['elements'][0]['distance']['text']).split(' ')[0]

                        data[state][town][zip_code]['date'] = date
                        data[state][town][zip_code]['day'] = week_day
                        data[state][town][zip_code]['times'][curr_time]['dur'] = duration_in_traffic
                        data[state][town][zip_code]['times'][curr_time]['dist'] = distance

                        if duration_in_traffic > data[state][town][zip_code]['max']:
                            data[state][town][zip_code]['max'] = duration_in_traffic
                        if duration_in_traffic < data[state][town][zip_code]['min']:
                            data[state][town][zip_code]['min'] = duration_in_traffic
                            data[state][town][zip_code]['total'] = data[state][town][zip_code][
                                                                       'total'] + duration_in_traffic

            print('Done processing for time ', curr_time)

            # if the last afternoon time, write results for the day
            if curr_time == commute_times[-1]:
                writeData = [[]]
                for town in data:
                    writeData[0] = [date, week_day]
                    currDf = pd.read_excel(os.path.join(COMMUTE_DATA_DIR, file_name + EXT), index_col=[0],
                                           sheet_name=town, engine='openpyxl')
                    col = currDf.columns
                    for t in data[state][town][zip_code]['times']:
                        writeData[0].append(data[state][town][zip_code]['times'][t]['dist'])
                        writeData[0].append(data[state][town][zip_code]['times'][t]['dur'])
                        if data[state][town][zip_code]['times'][t]['dur'] > 0: count += 1

                    writeData[0].append(data[state][town][zip_code]['max'])
                    writeData[0].append(data[state][town][zip_code]['min'])
                    writeData[0].append(data[state][town][zip_code]['total'] / count)
                    newDf = pd.DataFrame(writeData, columns=col)
                    frames.append(currDf)
                    frames.append(newDf)
                    entries[town] = pd.concat([currDf, newDf], ignore_index=True)
                    frames = []
                    count = 0
                    total = 0

                populateMaster(os.path.join(COMMUTE_DATA_DIR, file_name + EXT), entries)
                print('Wrote Data for the day to file')
                time.sleep(3600)
            else:
                time.sleep(60)
        else:
            print('Today is not a weekday')
            time.sleep(3600)

    '''
    frames = []
    entries = OrderedDict()

    for each in towns.split('|'):
        town = each.split(',')[0].strip()
        Data[town] = OrderedDict()

        Data[town].update({'date': 0, 'day': 0, 'times': OrderedDict()})
        for t in morningTimes:
            Data[town]['times'].update({t: {'dist':0, 'dur':0}})

        for t in afternoonTimes:
            Data[town]['times'].update({t: {'dist':0, 'dur':0}})

        Data[town].update({'max':0, 'min': 999, 'total': 0})

    # Mon = 0, Sun = 6
    currDay = datetime.datetime.today().weekday()  

    print('Started Processing Daily Commute')
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
                print('Processing for time ', currTime)
                date = str(datetime.datetime.now().date())
                if currTime in morningTimes:
                    commuteData = getCommuteData(towns, 'now', work)
                    for row in range(len(commuteData["rows"])):
                        origin = str(commuteData['origin_addresses'][row]).split(',')[0]
                        destination = commuteData['destination_addresses'][0]
                        duration = convertToMin(str(commuteData['rows'][row]['elements'][0]['duration']['text']))
                        duration_in_traffic = convertToMin(str(commuteData['rows'][row]['elements'][0]['duration_in_traffic']['text']))
                        distance = str(commuteData['rows'][row]['elements'][0]['distance']['text']).split(' ')[0]

                        Data[origin]['date'] = date
                        Data[origin]['day'] = weekDay
                        Data[origin]['times'][currTime]['dur'] = duration_in_traffic
                        Data[origin]['times'][currTime]['dist'] = distance

                        if duration_in_traffic > Data[origin]['max']:
                            Data[origin]['max'] = duration_in_traffic
                        if duration_in_traffic < Data[origin]['min']:
                            Data[origin]['min'] = duration_in_traffic
                            Data[origin]['total'] = Data[origin]['total'] + duration_in_traffic
                else:
                    commuteData = getCommuteData(work, 'now', towns)

                    for row in range(len(commuteData["destination_addresses"])):
                        origin = commuteData['origin_addresses'][0]
                        destination = str(commuteData['destination_addresses'][row]).split(',')[0]
                        duration = convertToMin(str(commuteData['rows'][0]['elements'][row]['duration']['text']))
                        duration_in_traffic = convertToMin(str(commuteData['rows'][0]['elements'][row]['duration_in_traffic']['text']))
                        distance = str(commuteData['rows'][0]['elements'][row]['distance']['text']).split(' ')[0]

                        Data[destination]['date'] = date
                        Data[destination]['day'] = weekDay
                        Data[destination]['times'][currTime]['dur'] = duration_in_traffic
                        Data[destination]['times'][currTime]['dist'] = distance

                        if duration_in_traffic > Data[destination]['max']:
                            Data[destination]['max'] = duration_in_traffic
                        if duration_in_traffic < Data[destination]['min']:
                            Data[destination]['min'] = duration_in_traffic
                        Data[destination]['total'] = Data[destination]['total'] + duration_in_traffic

                # if the last afternoon time, write results for the day
                if currTime == afternoonTimes[-1]:
                    writeData = [[]]
                    for town in Data:
                        writeData[0] = [date, weekDay]
                        currDf = pd.read_excel(os.path.join(COMMUTE_DATA, fileName + EXT), index_col=[0], sheet_name=town, engine='openpyxl')
                        col = currDf.columns
                        for t in Data[town]['times']:
                            writeData[0].append(Data[town]['times'][t]['dist'])
                            writeData[0].append(Data[town]['times'][t]['dur'])
                            if Data[town]['times'][t]['dur'] > 0: count += 1

                        writeData[0].append(Data[town]['max'])
                        writeData[0].append(Data[town]['min'])
                        writeData[0].append(Data[town]['total']/count)
                        newDf = pd.DataFrame(writeData, columns=col)
                        frames.append(currDf)
                        frames.append(newDf)
                        entries[town] = pd.concat([currDf, newDf], ignore_index=True)
                        frames = []
                        count = 0
                        total = 0

                    populateMaster(os.path.join(COMMUTE_DATA, fileName + EXT), entries)
                    print('Wrote Data for the day to file')
                    time.sleep(3600)

                print('Done processing for time ', currTime)
                time.sleep(60)
            else:
                time.sleep(60)
        else:
            print('Today is not a weekday')
            time.sleep(3600)
    '''
