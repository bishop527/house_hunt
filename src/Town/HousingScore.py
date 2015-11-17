'''
Created on Nov 17, 2015

@author: ad23883
@todo: 
'''

import pandas as pd
import numpy as np
import math

'''
Calculates the tax score for a town based on the tax rate passed in.
Score will be a positive or negative value between -10 to 10 with increments calculated based on the min and max values.
A tax value <= the min value will have a score of 10.
A tax value >= the max value will have a score of -10.
A tax value = the median value will have a score of 0.
'''
def calculateTaxScore(taxRate):
    score = 0
    minValue = 11.0
    maxValue = 21.0
    medianValue = 16.0
    maxScore = 10
    minScore = -10
    medianScore = 0
    
    step = int((maxValue-minValue)/10)
    score = ((medianValue - round(taxRate)))/step*2 
    
    # Restrict score to no greater then maxScore and no less then minScore
    if score > maxScore:
        score = score - (score % maxScore)
    elif score < minScore:
        score = score - (score % minScore)
        
    return score

'''
Calculates the housing score for a house price based on the house price passed in.
Score will be a positive or negative value between -10 to 10 with increments calculated based on the min and max values.
A house value <= the min value will have a score of 10.
A house value >= the max value will have a score of -10.
A house value = the median value will have a score of 0.
'''
def calculateHousePriceScore(houseCost):
    score = 0
    minValue = 350000
    maxValue = 450000
    medianValue = 400000
    maxScore = 10
    minScore = -10
    medianScore = 0
    
    step = int((maxValue-minValue)/10)    
    score = ((medianValue - houseCost))/step*2 
    
    # Restrict score to no greater then maxScore and no less then minScore
    if score > maxScore:
        score = maxScore
    elif score < minScore:
        score = minScore
    return score

'''
Read in data from the Master-Town_Data file and calculate tax and housing scores for each entry.
Housing scores will use the median list price for 3 bedroom properties. 
If there is not data for 3 bedroom properties then th median list price for All properties will be used.
'''
def calculateHousingScores():
    print 'Calculating Housing Scores'
    
    score = 0
    data = []
    columns = ['Zip Code', 'Town', 'Tax Rate', 'Median House Cost', 'Tax Score', 'Housing Score']
    houseData = pd.ExcelFile('Master-Town_Data-2015.xlsx').parse('Housing-Data')
    houseData.sort_values(by="Town", inplace=True)
    
    for row in range(len(houseData)-2):
        # Leading zero's are stripped off for some reason, so re-adding them
        zipCode = '0'+str(houseData.iloc[row, 0])
        town = houseData.iloc[row, 1]
        taxRate = houseData.iloc[row, 3]
        houseCost = houseData.iloc[row, 8]
        # if no 3 bedroom property value, use All Properties value
        if np.isnan(houseCost):
            if not np.isnan(houseData.iloc[row, 5]):
                houseCost = houseData.iloc[row, 5]
            # if All properties value is also NaN, skip this row
            else:
                continue
            
        taxScore = calculateTaxScore(taxRate)
        houseScore = calculateHousePriceScore(houseCost)
        data.append([zipCode, town, taxRate, houseCost, taxScore, houseScore])
        
    df = pd.DataFrame(data, columns=columns)
    writer = pd.ExcelWriter('Master_Scores-2015.xlsx', engine="openpyxl")
    df.to_excel(writer,"Housing-Scores")
    writer.save()
    