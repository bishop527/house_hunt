'''
Created on Nov 23, 2015

@author: ad23883
'''

import pandas as pd
from School.ParseSchoolData import districtLookup
from utils import *

priorities = {'School': [5],
            'Commute':  [2],
            'House':    [3]}

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
    weight = priorities[k][0]
    score = (weight * v)
        
    return score

def calculateCombinedScores():
    fileName = 'Master_Scores-2015'
    data = {}
    columns = ['District', 'Distance', 'Avg House Cost', 'Tax Rate', 'Commute Score', 'House Score', 'School Score', 'Combined Score']
    
    calculatePriorityWeights()
    
    commuteScores = pd.read_excel(fileName+ext, sheetname='Commute-Scores', header=0)
    schoolScores = pd.read_excel(fileName+ext, sheetname='School-Scores', header=0)
    houseScores = pd.read_excel(fileName+ext, sheetname='Housing-Scores', header=0)
    schoolData = pd.read_excel(os.path.join(schoolDataLocation, 'Master-School_Data-2015'+ext), sheetname='Admin-School', header=0)

    # Parse Commute Scores, get town name and weighted score
    for row in range(len(commuteScores)):
        town = commuteScores.index.values[row]
        
        data[town] = [0, 0, 0, 0, 0, 0, 0, 0]
        distance = commuteScores.iloc[row, 0]
        commuteScore = commuteScores.iloc[row, 2]

        data[town][1] = distance
        data[town][4] = commuteScore
        if town in houseScores.index.values:
            taxRate = houseScores['Tax Rate'][town]
            houseCost = houseScores['Median House Cost'][town]
            houseScore = houseScores['Weighted Score'][town]
            
            data[town][2] = houseCost
            data[town][3] = taxRate
            data[town][5] = houseScore

        else:
            print 'Skipping town', town
            del data[town]
            continue
        
        # Look for town in School Scores
        if town in schoolScores.index.values:
            data[town][0] = town
            data[town][6] = schoolScores['Weighted Score'][town]
        # if not in school scores, look in school data
        else:
            district = schoolData[schoolData['Town'] == town].District.values
            if len(district) > 0 and district[0] in schoolScores.index.values:
                data[town][0] = district[0]
                data[town][6] = schoolScores['Weighted Score'][district[0]]
            else:
                district = districtLookup(town)
                if district != None and district in schoolScores.index.values:
                    data[town][0] = district
                    data[town][6] = schoolScores['Weighted Score'][district]
                else:
                    print 'Unable to find', town, 'in School Scores, School Data, or District Lookup'
                    print 'Skipping town', town
                    del data[town]
        
        if town in data:   
            currCombinedScore = float(data[town][-1])
            currCombinedScore += calculateWeightedScore(['Commute', data[town][4]])
            currCombinedScore += calculateWeightedScore(['House', data[town][5]])
            currCombinedScore += calculateWeightedScore(['School', data[town][6]])
            data[town][-1] = round(currCombinedScore, 2)
    
    df = pd.DataFrame.from_items(data.items(), columns=columns, orient='index')    
        
    return df
