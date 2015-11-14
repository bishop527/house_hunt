'''
Created on Nov 12, 2015

@author: ad23883
'''
import urllib
import urllib2
import xml.etree.ElementTree
from bs4 import BeautifulSoup
import pandas as pd

dataLocation = "data/town/"
ext = ".xlsx"

truliaKey = '9z8g9yszfkukswpj5q3ry5a4'

def getTruliaCities(state='MA'):
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

def getTruliaZipCodeStats(zip, startDate, endDate):
    
    fileName = 'House_Data-2015'+ext
    
    data = [['NA','NA','NA','NA','NA','NA','NA','NA','NA']]
    
    medianListPrice = ''
    avgListPrice = ''
    #columns = ['Zip, All-Avg List, All-Med List, 3-Avg List, 3-Med List, 2-Avg List, 2-Med List, 1-Avg List, 1-Med List']
    columns = pd.MultiIndex.from_tuples([('Zip', ''),
                                         ('All Properties', 'Avg List Price'),('All Properties', 'Median List Price'),
                                         ('3 Bedroom', 'Avg List Price'),('3 Bedroom', 'Median List Price'),
                                         ('2 Bedroom', 'Avg List Price'),('2 Bedroom', 'Median List Price'),
                                         ('1 Bedroom', 'Avg List Price'),('1 Bedroom', 'Median List Price')])
         
    url_base = 'http://api.trulia.com/webservices.php?library=TruliaStats&function=getZipCodeStats&'
    url = url_base+'zipCode='+zip+'&startDate='+startDate+'&endDate='+endDate+'&apikey='+truliaKey
    print url

    e = BeautifulSoup(urllib2.urlopen(url).read(), 'lxml')

    data[0][0] = zip
    
    for each in e.findAll('subcategory'):
        if each.type.text == 'All Properties':
            avgListPrice = each.averagelistingprice.text
            data[0][1] = avgListPrice
            medianListPrice = each.medianlistingprice.text
            data[0][2] = medianListPrice
        if each.type.text == '3 Bedroom Properties':
            avgListPrice = each.averagelistingprice.text
            data[0][3] = avgListPrice
            medianListPrice = each.medianlistingprice.text
            data[0][4] = medianListPrice
        if each.type.text == '2 Bedroom Properties':
            avgListPrice = each.averagelistingprice.text
            data[0][5] = avgListPrice
            medianListPrice = each.medianlistingprice.text
            data[0][6] = medianListPrice
        if each.type.text == '1 Bedroom Properties':
            avgListPrice = each.averagelistingprice.text
            data[0][7] = avgListPrice
            medianListPrice = each.medianlistingprice.text
            data[0][8] = medianListPrice
    
    df = pd.DataFrame(data, columns=columns)
    
    writer = pd.ExcelWriter(dataLocation+fileName, engine="openpyxl")
    df.to_excel(writer,"Sheet1")
    writer.save()
    
    return df