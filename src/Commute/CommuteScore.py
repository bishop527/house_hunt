'''
Created on Nov 17, 2015

@author: ad23883
@todo: 
'''
import pandas as pd

'''
Calculates the commute score for a distance value passed in.
Score will be a positive or negative value between -10 to 10 with increments calculated based on the min and max values.
A commute value <= the min value will have a score of 10.
A commute value >= the max value will have a score of -10.
A commute value = the median value will have a score of 0.
'''
def calculateCommuteDistanceScore(distance):
    score = 0
    minValue = 10
    maxValue = 60
    medianValue = 35
    maxScore = 10
    minScore = -10
    medianScore = 0
    
    step = int((maxValue-minValue)/10)    
    score = int((medianValue - round(distance)))/step*2 
    
    # Restrict score to no greater then maxScore and no less then minScore
    if score > maxScore:
        score = maxScore
    elif score < minScore:
        score = minScore
    return score

def calculateCommuteScores():
    print 'Calculating Commute Scores'
    
    score = 0
    data = []
    columns = ['Town', 'Distance', 'Commute Score']
    commuteData = pd.read_excel('Master-Commute_Data-2015.xlsx', header=0)
    
    for row in range(len(commuteData)):
        town = commuteData.iloc[row, 0]
        distance = commuteData.iloc[row, 1]

        commuteScore = calculateCommuteDistanceScore(distance)
        data.append([town, distance, commuteScore])
        
    df = pd.DataFrame(data, columns=columns)
    writer = pd.ExcelWriter('Master_Scores-2015.xlsx', engine="openpyxl")
    df.to_excel(writer,"Commute-Scores")
    writer.save()
