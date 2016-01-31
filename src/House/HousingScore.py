'''
Created on Nov 17, 2015

@author: ad23883
@todo: 
'''

import pandas as pd
import numpy as np
from utils import *

priorities = {'House Cost': [8],
              'Tax Cost':   [2]}

'''
This method uses relative frequency to assign a weight to each item in the 
priorities list. These weights will then used to calculate the total score of 
each school.
'''
def calculatePriorityWeights():
    sum = 0.0
        
    # calculate sum
    for k, v in priorities.iteritems():
        sum += v[0]
    # calculate weight
    for k, v in priorities.iteritems():
        priorities[k].append(round(v[0]/sum,2))

def calculateWeightedScore(value):
    k = value[0]
    v = value[1]
    weight = priorities[k][1]
    score = (weight * v)
        
    return score

'''
Calculates the tax score for a town based on the tax rate passed in.
Score will be a positive or negative value between -10 to 10 with increments calculated based on the min and max values.
A tax value <= the min value will have a score of 10.
A tax value >= the max value will have a score of -10.
A tax value = the median value will have a score of 0.
'''
def calculateTaxScore(taxRate):

    minValue = 11.0
    maxValue = 21.0
    medianValue = (maxValue + minValue)/2

    step = int((maxValue-minValue)/10)
    score = int((medianValue - round(taxRate))/step)*2 
        
    #return normalizeScore(score)
    return score

'''
Calculates the housing score for a house price based on the house price passed in.
Score will be a positive or negative value between -10 to 10 with increments calculated based on the min and max values.
A house value <= the min value will have a score of 10.
A house value >= the max value will have a score of -10.
A house value = the median value will have a score of 0.
'''
def calculateHousePriceScore(houseCost):
    
    minValue = 320000
    maxValue = 470000
    minThreshold = 285000
    maxThreshold = 450000
    
    if houseCost > minThreshold and houseCost < maxThreshold:
        medianValue = (maxValue + minValue) / 2
        step = int((maxValue-minValue)/10)    
        score = int((medianValue - houseCost)/step)*2 
    else:
        score = -100
        
    #return normalizeScore(score)
    return score

def calculateHouseScores():
    print 'Calculating House Scores'
    fileName = 'Master-House_Data-2015'
    data = {}
    
    calculatePriorityWeights()
        
    columns = ['Tax Rate', 'Median House Cost', 'Tax Score', 'Housing Score', 'Weighted Score']
    houseData = pd.read_excel(os.path.join(houseDataLocation, fileName+ext), sheetname='House-Data')

    for row in range(len(houseData)):
        taxScore = 0
        houseScore = 0
        weightedScore = 0
        
        town = houseData.iloc[row, 0]

        taxRate = houseData.iloc[row, 1]
        medianHouseCost = houseData.iloc[row, 2]

        taxScore = calculateTaxScore(taxRate)
        weightedScore = calculateWeightedScore(['Tax Cost', taxScore])
    
        houseScore = calculateHousePriceScore(medianHouseCost)
        weightedScore += calculateWeightedScore(['House Cost', houseScore])
        
        data[town] = [taxRate, medianHouseCost, taxScore, houseScore, round(weightedScore, 2)]
            
    df = pd.DataFrame.from_items(data.items(), columns=columns, orient='index')
    
    return df

'''
@deprecated: No longer use Trulia API methods. Use MLS data instead
Read in data from the Master-Town_Data file and calculate tax and housing scores for each entry.
Housing scores will use the median list price for 3 bedroom properties. 
If there is not data for 3 bedroom properties then th median list price for All properties will be used.
'''
def calculateTruliaScores():
    print 'Calculating Housing Scores'
    fileName = 'Master-Town_Data-2015.xlsx'
    score = 0
    data = {}
    calculatePriorityWeights()
        
    columns = ['Tax Rate', 'Median House Cost', 'Tax Score', 'Housing Score', 'Weighted Score']
    houseData = pd.ExcelFile(os.path.join(houseDataLocation, fileName+ext)).parse('All Properties Housing Data')
    houseData.sort_values(by="House", inplace=True)
    
    for row in range(len(houseData)):
        town = houseData.iloc[row, 0]
        taxRate = houseData.iloc[row, 2]
        medianHouseCost = houseData.iloc[row, 5]
        # if no 3 bedroom property value, use All Properties value
        if np.isnan(medianHouseCost):
            continue
        
        taxScore = calculateTaxScore(taxRate)
        weightedScore = calculateWeightedScore(['Tax Cost', taxScore])
        
        houseScore = calculateHousePriceScore(medianHouseCost)
        weightedScore += calculateWeightedScore(['House Cost', houseScore])
        
        data[town] = [taxRate, medianHouseCost, taxScore, houseScore, round(weightedScore, 2)]
            
    df = pd.DataFrame.from_items(data.items(), columns=columns, orient='index')
    
    return df
    