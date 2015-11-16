'''
Created on Nov 12, 2015

@author: ad23883
@todo: 
'''
import urllib2
from bs4 import BeautifulSoup
import pandas as pd
import time
from TownData import townLookup
from Town.TownData import countyLookup, taxRateLookup

dataLocation = "data/town/"
ext = ".xlsx"

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

def getTruliaZipCodeStats(zips, startDate, endDate):
    print "        Downloading Trulia Housing Data"
    fileName = 'House_Data-2015'+ext
    data = []
    retry = []
    
    medianListPrice = ''
    avgListPrice = ''
    columns = pd.MultiIndex.from_tuples([('Zip',''),('Town',''),('County',''),('Tax Rate', ''),
                                         ('All Properties', 'Avg List Price'),('All Properties', 'Median List Price'),('All Properties', 'Median Tax Cost'),
                                         ('3 Bedroom', 'Avg List Price'),('3 Bedroom', 'Median List Price'),('3 Bedroom', 'Median Tax Cost'),
                                         ('2 Bedroom', 'Avg List Price'),('2 Bedroom', 'Median List Price'),('2 Bedroom', 'Median Tax Cost'),
                                         ('1 Bedroom', 'Avg List Price'),('1 Bedroom', 'Median List Price'),('1 Bedroom', 'Median Tax Cost'),])
    #cols = product(['All Properties', '3 Bedroom', '2 Bedroom', '1 Bedroom'], ['Avg List Price', 'Median List Price'])
    #columns = pd.MultiIndex.from_tuples(list(cols))
    
    url_base = 'http://api.trulia.com/webservices.php?library=TruliaStats&function=getZipCodeStats&'
    
    # Iterate through all zips passed in
    for row in range(len(zips)):
        if row % 2 == 0:
            time.sleep(1)

        zipCode = zips[row]
        town = townLookup(zipCode)
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
    
    writer = pd.ExcelWriter(dataLocation+fileName, engine="openpyxl")
    df.to_excel(writer,"Sheet1")
    writer.save()
    
    return df