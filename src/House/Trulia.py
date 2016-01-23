'''
Created on Nov 12, 2015

@author: ad23883
@todo: 
'''
import urllib2
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import time
from House.HouseData import countyLookup, taxRateLookup, zipLookup, townExists
from utils import *
import os

truliaKey = '9z8g9yszfkukswpj5q3ry5a4'

def getTruliaCities(state='MA'):
    print "        Downloading Trulia data for cities in", state

    data = []
    
    url_base = 'http://api.trulia.com/webservices.php?library=LocationInfo&function=getCitiesInState&'
    url = url_base+'state='+state+'&apikey='+truliaKey

    e = BeautifulSoup(urllib2.urlopen(url).read(), 'lxml')

    for each in e.findAll('city'):
        data.append(each.find('name').text)
    
    return data

def getTruliaNeighborhoods(city, state='MA'):
    data = []
    
    url_base = 'http://api.trulia.com/webservices.php?library=LocationInfo&function=getNeighborhoodsInCity&'
    url = url_base+'state='+state+'&city='+city+'&apikey='+truliaKey
    print url

    e = BeautifulSoup(urllib2.urlopen(url).read(), 'lxml')

    for each in e.findAll('neighborhood'):
        data.append(each)
    
    return data

def getTruliaZipCodesInState(state='MA'):
    print "        Downloading Trulia zip codes for", state
    data = []
    
    url_base = 'http://api.trulia.com/webservices.php?library=LocationInfo&function=getZipCodesInState&'
    url = url_base+'state='+state+'&apikey='+truliaKey

    e = BeautifulSoup(urllib2.urlopen(url).read(), 'lxml')

    for each in e.findAll('zipcode'):
        data.append(each.find('name').text)
    
    return data

'''
This method pulls data from Trulia.com using their API. 
The API can only do lookups by zip code, not by town name. This causes problems especially for 
towns with multiple zip codes and the data received does not match with the data shown on the
main Trulia.com website in an immediately obvious way. 
Decided to move away from collecting data in this way. Keeping the method here for historical
purposes.
'''
def getCombinedTruliaZipCodeStats(startDate, endDate):
    print "        Downloading Trulia Housing Data"
    data = []
    retry = []
    finalAverageListPrice = 0
    finalMedianListPrice = 0
    
    columns = ['House', 'Zip Code', 'Tax Rate', 'Avg List Price', 'Avg Tax Cost', 'Median List Price', 'Median Tax Cost']
        
    url_base = 'http://api.trulia.com/webservices.php?library=TruliaStats&function=getZipCodeStats&'

    townData = pd.read_excel(os.path.join(townDataLocation, 'Town_Admin-2015'+ext), header=0)
    for row in range(len(townData)):
        count = 0
        finalAverageListPrice = 0
        finalAverageTaxCost = 0
        finalMedianListPrice = 0
        finalMedianTaxCost = 0
        
        town = townData.iloc[row, 0]

        # get all zips in current row seperated by comma and strip tail comma
        zipCodes = townData.iloc[row, 1].split(',')[:-1]
        taxRate = townData.iloc[row, 3]
        
        # get stats for each zip
        for zipCode in zipCodes:
            totalAverageListPrice = 0
            totalAverageTaxCost = 0
            totalMedianListPrice = 0
            totalMedianTaxCost = 0
            
            url = url_base+'zipCode='+zipCode+'&startDate='+startDate+'&endDate='+endDate+'&apikey='+truliaKey
            try:
                time.sleep(1)
                e = BeautifulSoup(urllib2.urlopen(url).read(), 'lxml')
                
                for each in e.findAll('subcategory'):
                    averageListPrice = int(each.averagelistingprice.text)
                    medianListPrice = int(each.medianlistingprice.text)
                    averageTaxCost = round(taxRate*(averageListPrice/1000), 2)
                    medianTaxCost = round(taxRate*(medianListPrice/1000), 2)
                    
                    if np.isnan(medianListPrice):
                        continue
                    
                    if each.type.text == 'All Properties' and count < 12:
                        totalAverageListPrice += averageListPrice
                        totalAverageTaxCost += averageTaxCost
                        totalMedianListPrice += medianListPrice
                        totalMedianTaxCost += medianTaxCost
                        count += 1
                        
                if count > 0:
                    totalAverageListPrice = totalAverageListPrice / count
                    totalAverageTaxCost = totalAverageTaxCost / count
                    totalMedianListPrice = totalMedianListPrice / count
                    totalMedianTaxCost = totalMedianTaxCost / count
                    if totalAverageListPrice > finalAverageListPrice:
                        finalAverageListPrice = totalAverageListPrice
                        finalAverageTaxCost = totalAverageTaxCost
                    if totalMedianListPrice > finalMedianListPrice:
                        finalMedianListPrice = totalMedianListPrice
                        finalMedianTaxCost = totalMedianTaxCost    
                        
            except urllib2.HTTPError as e:
                print "HTTP Error, skipping zip ", zipCode
                retry.append(zipCode)
        
        if count > 0:
            data.append([town, zipCodes, taxRate, finalAverageListPrice, finalAverageTaxCost, finalMedianListPrice, finalMedianTaxCost])
            count = 0
            
    df = pd.DataFrame(data, columns=columns)
#     writer = pd.ExcelWriter(dataLocation+fileName, engine="openpyxl")
#     df.to_excel(writer,"Sheet1")
#     writer.save()
    
    return df

def getTruliaZipCodeStats(zips, startDate, endDate):
    print "        Downloading Trulia Housing Data"
    fileName = 'House_Data-2015'+ext
    data = []
    retry = []
    
    medianListPrice = ''
    avgListPrice = ''
    columns = pd.MultiIndex.from_tuples([('Zip',''),('House',''),('County',''),('Tax Rate', ''),
                                         ('All Properties', 'Avg List Price'),('All Properties', 'Median List Price'),('All Properties', 'Median Tax Cost'),
                                         ('3 Bedroom', 'Avg List Price'),('3 Bedroom', 'Median List Price'),('3 Bedroom', 'Median Tax Cost'),
                                         ('2 Bedroom', 'Avg List Price'),('2 Bedroom', 'Median List Price'),('2 Bedroom', 'Median Tax Cost'),
                                         ('1 Bedroom', 'Avg List Price'),('1 Bedroom', 'Median List Price'),('1 Bedroom', 'Median Tax Cost'),])
    
    url_base = 'http://api.trulia.com/webservices.php?library=TruliaStats&function=getZipCodeStats&'
        
    # Iterate through all zips passed in
    for row in range(len(zips)):
        if row % 2 == 0:
            time.sleep(1)

        zipCode = zips[row]
        town = zipLookup(zipCode)
        
        if not townExists(town):
            print town, ' is not in the list'
            
        taxRate = float(taxRateLookup(town))
        county = countyLookup(zipCode)
        
        # Need to initialize data array for 15 positions because not all city entries contain data for all 15 values
        data.append([zipCode, town, county, taxRate, 'NA','NA','NA','NA','NA','NA','NA','NA','NA','NA','NA','NA'])
        
        url = url_base+'zipCode='+zipCode+'&startDate='+startDate+'&endDate='+endDate+'&apikey='+truliaKey
        try:
            e = BeautifulSoup(urllib2.urlopen(url).read(), 'lxml')
            
            for each in e.findAll('subcategory'):
                avgListPrice = float(each.averagelistingprice.text)
                medianListPrice = float(each.medianlistingprice.text)
                medianTaxCost = round(taxRate*(medianListPrice/1000), 2)

                if each.type.text == 'All Properties':
                    data[row][4] = avgListPrice
                    data[row][5] = medianListPrice
                    data[row][6] = medianTaxCost
                elif each.type.text == '3 Bedroom Properties':
                    data[row][7] = avgListPrice
                    data[row][8] = medianListPrice
                    data[row][9] = medianTaxCost
                elif each.type.text == '2 Bedroom Properties':
                    data[row][10] = avgListPrice
                    data[row][11] = medianListPrice
                    data[row][12] = medianTaxCost
                elif each.type.text == '1 Bedroom Properties':
                    data[row][13] = avgListPrice
                    data[row][14] = medianListPrice
                    data[row][15] = medianTaxCost
            
        except urllib2.HTTPError as e:
            print "HTTP Error, skipping zip ", zipCode
            retry.append(zipCode)
            
    print "            Skipped ", len(retry), "zip codes"
    df = pd.DataFrame(data, columns=columns)
    
#     writer = pd.ExcelWriter(dataLocation+fileName, engine="openpyxl")
#     df.to_excel(writer,"Sheet1")
#     writer.save()
    
    return df