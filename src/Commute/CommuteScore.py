'''
Created on Nov 17, 2015

@author: ad23883
@todo: 
'''
import pandas as pd
from utils import *

fileName = 'Master-Commute_Data-2015'

priorities = {'Distance': [3],
              'Duration': [7]}

'''
THis method uses relative frequency to assign a weight to each item in the 
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
Calculates the commute score for a distance value passed in.
Score will be a positive or negative value between -10 to 10 with increments calculated based on the min and max values.
A commute value <= the min value will have a score of 10.
A commute value >= the max value will have a score of -10.
A commute value = the median value will have a score of 0.
'''
def calculateCommuteDistanceScore(distance):
    
    minValue = 10
    maxValue = 60
    threshold = 40
    medianValue = (maxValue + minValue) / 2
    
    if distance < threshold:
        step = int((maxValue-minValue)/10)    
        score = int((medianValue - round(distance))/step)*2 
    else:
        score = -100
        
    return score

'''
Calculates the commute score for a distance value passed in.
Score will be a positive or negative value between -10 to 10 with increments calculated based on the min and max values.
A commute value <= the min value will have a score of 10.
A commute value >= the max value will have a score of -10.
A commute value = the median value will have a score of 0.
'''
def calculateCommuteDurationScore(duratoin):
    
    minValue = 10
    maxValue = 70
    threshold = 60
    medianValue = (maxValue + minValue) / 2
    
    if duratoin < threshold:
        step = int((maxValue-minValue)/10)    
        score = int((medianValue - round(duratoin))/step)*2 
    else:
        score = -100
        
    return score

def calculateCommuteScores():
    print 'Calculating Commute Scores'

    data = {}
    columns = ['Distance', 'Duration', 'Distance Score', 'Duration Score', 'Weighted Score']
    calculatePriorityWeights()
    
    commuteData = pd.read_excel(os.path.join(commuteDataLocation, fileName+ext), header=0)
    
    for row in range(len(commuteData)):
        distanceScore = 0
        durationScore = 0
        weightedScore = 0
        
        town = commuteData.iloc[row, 0]
        if not town in data:
            data[town] = [0, 0, 0, 0, 0]
            
        distance = commuteData.iloc[row, 1]
        distanceScore = calculateCommuteDistanceScore(distance)
        duration = commuteData.iloc[row,2]
        durationScore = calculateCommuteDurationScore(duration)
        
        weightedScore += calculateWeightedScore(['Distance', distanceScore])
        weightedScore += calculateWeightedScore(['Duration', durationScore])
        data[town] = [distance, duration, distanceScore, durationScore, round(weightedScore, 2)]
        
    df = pd.DataFrame.from_items(data.items(), columns=columns, orient='index')
    
    return df
