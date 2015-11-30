'''
Created on Nov 17, 2015

@author: ad23883
'''
import pandas as pd
import numpy as np
from utils import normalizeScore

dataLocation = 'data/school/'
fileName = 'Master-School_Data-2015'
ext = '.xlsx'

priorities = {'Higher Ed':        [10],
              'SAT':              [9],
              'MCAS':             [8],
              'SPED %':           [7],
              'Accnt Level':      [6],
              'Grad %':           [5],
              'Rank':             [4],
              'Parent Involve':   [3],
              'Class Size':       [2]}

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

def calculateAccountabilityScore(value):
    score = 0
    
    if value == 'Level 5':
        score = -10
    if value == 'Level 4':
        score = -5
    elif value == 'Level 3':
        score = 0
    elif value == 'Level 2':
        score = 5
    elif value == 'Level 1':
        score = 10
    # level most likely set to insufficient data. Score as 0 so doesn't help nor harm
    else:
        score = 0
    
    #return normalizeScore(score)
    return score
    
def calculateClassSizeScore(value):
    minValue = 12
    maxValue = 24
    medianValue = (maxValue+minValue)/2

    step = int((maxValue-minValue)/10)    
    score = int((medianValue - round(value))/step)*2 
     
#    return normalizeScore(score)
    return score

def calculateSPEDPercScore(value):
    minValue = 8.0
    maxValue = 24.0
    medianValue = (maxValue+minValue)/2

    step = ((maxValue-minValue)/10)    
    score = int((medianValue - round(value))/step)*2 
     
#    return normalizeScore(score)
    return score

def calculateDropoutScore(value):
    minValue = 0.0
    maxValue = 5.0
    medianValue = (maxValue+minValue)/2
    
    step = (maxValue-minValue)/10    
    score = int((medianValue - round(value))/step)*2 
    
#    return normalizeScore(score)
    return score

def calculateGraduationScore(value):
    minValue = 80.0
    maxValue = 100
    medianValue = (maxValue+minValue)/2
    
    step = (maxValue-minValue)/10    
    score = int((round(value) - medianValue)/step)*2 
    
#    return normalizeScore(score)
    return score

def calculateHigherEdScore(value):
    minValue = 70.0
    maxValue = 90
    threshold = 70
    medianValue = (maxValue+minValue)/2

    if value > threshold:
        step = (maxValue-minValue)/10    
        score = int((round(value) - medianValue)/step)*2 
    else:
        score = -100
        
#    return normalizeScore(score)
    return score

def calculateMCASScore(category, value):

    if category == 'Prof_Adv':
        minValue = 50
        maxValue = 90
    elif category == 'NI':
        minValue = 45
        maxValue = 10
    elif category == 'W/F':
        minValue = 10
        maxValue = 0
    
    medianValue = (maxValue+minValue)/2
    
    if category == 'Prof_Adv': 
        step = int(maxValue-minValue)/10    
        score = int((round(value) - medianValue)/step)*2 
    else:
        step = int(minValue-maxValue)/10    
        score = int((medianValue-round(value))/step)*2 
    
#    return normalizeScore(score)
    return score

def calculateSATScore(value):
    minValue = 1300
    maxValue = 1800
    medianValue = (maxValue+minValue)/2
    
    step = int(maxValue-minValue)/10    
    score = int((round(value) - medianValue)/step)*2 
    
#    return normalizeScore(score)
    return score

def calculateParentInvolveScore(value):
    minValue = 0
    maxValue = 100
    medianValue = (maxValue+minValue)/2

    step = (maxValue-minValue)/10    
    score = int((round(value) - medianValue)/step)*2 
    
#    return normalizeScore(score)
    return score

def calculateSalaryScore(value):
    minValue = 50000
    maxValue = 90000
    medianValue = (maxValue+minValue)/2

    step = (maxValue-minValue)/10    
    score = int((round(value) - medianValue)/step)*2 
    
#    return normalizeScore(score)
    return score

def calculateRankScore(value):
    minValue = 249
    maxValue = 1
    medianValue = (maxValue+minValue)/2

    step = (minValue-maxValue)/10    
    score = int((medianValue-round(value))/step)*2 
    
#    return normalizeScore(score)
    return score

def calculateSchoolScores():
    print 'Calculating School Scores'
    
    data = {}
    columns = ['Accnt Level ', 'Class Size', 'Parent Involve', 'SPED %', 'Dropout %', 'Grad %', 'Higher Ed', 'MCAS', 'SAT', 'School Rank', 'Weighted Score']
        
    calculatePriorityWeights()
    
    # Accountability Level Score
    accntData = pd.read_excel(dataLocation+fileName+ext, sheetname='Accountability-District', header=0)    
    for row in range(len(accntData)):
        district = accntData.iloc[row, 0]
        level = accntData.iloc[row, 1]
        accntScore = calculateAccountabilityScore(level)
        
        data[district] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        data[district][0] = accntScore
        currScore = float(data[district][-1])
        currScore += calculateWeightedScore(['Accnt Level', accntScore])
        data[district][-1] = round(currScore, 2)
    
    # Class Size and SPED % Score
    classSizeData = pd.read_excel(dataLocation+fileName+ext, sheetname='Class_Size-District', header=0)
    
    # Class Size
    for row in range(len(classSizeData)):
        district = classSizeData.iloc[row, 0]
        classSize = classSizeData.iloc[row, 1]
        if np.isnan(classSize):
            continue
        classSizeScore = calculateClassSizeScore(classSize)
        
        if not district in data:
            print 'ClassSize: Skipping ',district
            continue
            
        data[district][1] = classSizeScore
        currScore = float(data[district][-1])
        currScore += calculateWeightedScore(['Class Size', classSizeScore])
        data[district][-1] = round(currScore, 2)
        
    # SPED %
    for row in range(len(classSizeData)):
        district = classSizeData.iloc[row, 0]
        spedPerc = classSizeData.iloc[row, 2]
        if np.isnan(spedPerc):
            continue
        spedPercScore = calculateSPEDPercScore(spedPerc)
        
        if not district in data:
            print 'SPED %: Skipping ',district
            continue

        data[district][3] = spedPercScore
        currScore = float(data[district][-1])
        currScore += calculateWeightedScore(['SPED %', spedPercScore])
        data[district][-1] = round(currScore, 2)
    
    # SPED Parent Involvement Score
    parentData = pd.read_excel(dataLocation+fileName+ext, sheetname='SPED-Performance', header=0, skiprows=2)
    
    for row in range(len(parentData)):
        district = parentData.iloc[row, 1]
        parentPerc = parentData.iloc[row, 13]
        if parentPerc != 'NR' and parentPerc != '-':
            parentPerc = float(parentPerc)
            if np.isnan(parentPerc):
                continue
            parentScore = calculateParentInvolveScore(parentPerc)
        else:
            parentScore = -10
            
        if not district in data:
            print 'Parent: Skipping ',district
            continue

        data[district][2] = parentScore
        currScore = float(data[district][-1])
        currScore += calculateWeightedScore(['Parent Involve', parentScore])
        data[district][-1] = round(currScore, 2)
            
    # Dropout Rate Score
#     dropoutData = pd.read_excel(dataLocation+fileName+ext, sheetname='Dropout-District', header=0)
#     
#     for row in range(len(dropoutData)):
#         district = dropoutData.iloc[row, 0]
#         dropPerc = dropoutData.iloc[row, 3]
#         if not np.isnan(dropPerc):
#             dropoutScore = calculateDropoutScore(dropPerc)
#         else:
#             dropoutScore = 0
#             
#         if not district in data:
#             print 'Dropout: Skipping ',district
#             continue
#         
#         data[district][4] = dropoutScore
#         currScore = float(data[district][-1])
#         currScore += calculateWeightedScore(['Dropout %', dropoutScore])
#         data[district][-1] = round(currScore, 2)

    # Graduation Rate Score
    graduationData = pd.read_excel(dataLocation+fileName+ext, sheetname='GraduationRates-District', header=0)
    
    for row in range(len(graduationData)):
        district = graduationData.iloc[row, 0]
        gradPerc = graduationData.iloc[row, 2]
        if not np.isnan(gradPerc):
            gradScore = calculateGraduationScore(gradPerc)
        else:
            gradScore = 0
            
        if not district in data:
            print 'Grad: Skipping ',district
            continue
        
        data[district][5] = gradScore
        currScore = float(data[district][-1])
        currScore += calculateWeightedScore(['Grad %', gradScore])
        data[district][-1] = round(currScore, 2)

    # Higher Education Rate Score
    higherEdData = pd.read_excel(dataLocation+fileName+ext, sheetname='HigherEd-District', header=0)
    
    for row in range(len(higherEdData)):
        district = higherEdData.iloc[row, 0]
        higherEdPerc = higherEdData.iloc[row, 3]
        if not np.isnan(higherEdPerc):
            higherEdScore = calculateHigherEdScore(higherEdPerc)
        else:
            higherEdScore = 0
            
        if not district in data:
            print 'HigherEd: Skipping ',district
            continue
                    
        data[district][6] = higherEdScore
        currScore = float(data[district][-1])
        currScore += calculateWeightedScore(['Higher Ed', higherEdScore])
        data[district][-1] = round(currScore, 2)
        
    # MCAS Score
    mcasData = pd.ExcelFile(dataLocation+fileName+ext).parse('MCAS-District')
    mcasData.sort_values(by="District", inplace=True)
    
    totalELA = 0
    totalMTH = 0
    totalSCI = 0
    countELA = 0
    countMTH = 0
    countSCI = 0        
    for row in range(len(mcasData)):        
        district = mcasData.iloc[row, 0]

        subject = mcasData.iloc[row, 2]
        
        # calculate Prof+Adv score
        prof_advValue = mcasData.iloc[row, 4]
        if not np.isnan(prof_advValue):
            prof_advScore = calculateMCASScore('Prof_Adv', prof_advValue)
        else:
            prof_advScore = 0
            
        if subject == 'ELA':
            totalELA += prof_advScore
            countELA += 1
        elif subject == 'MTH':
            totalMTH += prof_advScore
            countMTH += 1            
        elif subject == 'SCI':
            totalSCI += prof_advScore
            countSCI += 1  

        # calculate NI score
        niValue = mcasData.iloc[row, 10]
        if not np.isnan(niValue):
            niScore = calculateMCASScore('NI', niValue)
        else:
            niScore = 0
            
        if subject == 'ELA':
            totalELA += niScore
            countELA += 1
        elif subject == 'MTH':
            totalMTH += niScore
            countMTH += 1            
        elif subject == 'SCI':
            totalSCI += niScore
            countSCI += 1              

        # calculate W/F score
        wfValue = mcasData.iloc[row, 12]
        if not np.isnan(wfValue):
            wfScore = calculateMCASScore('W/F', wfValue)
        else:
            wfScore = 0
            
        if subject == 'ELA':
            totalELA += wfScore
            countELA += 1
        elif subject == 'MTH':
            totalMTH += wfScore
            countMTH += 1            
        elif subject == 'SCI':
            totalSCI += wfScore
            countSCI += 1      
        
        # check if the next row is for the same district. 
        # If not, calculate combined score and reset all variables and append data    
        if row < (len(mcasData)-1):
            if mcasData.iloc[row+1, 0] == district:
                continue

            if district in data:     
                mcasScore = (totalELA+totalMTH+totalSCI) / 3
                #mcasScore = normalizeScore((totalELA+totalMTH+totalSCI) / 3)
                data[district][7] = mcasScore
                currScore = float(data[district][-1])
                currScore += calculateWeightedScore(['MCAS', mcasScore])
                data[district][-1] = round(currScore, 2)
            else:
                print 'MCAS: Skipping ',district
                continue
            
            totalELA = 0
            totalMTH = 0
            totalSCI = 0
            countELA = 0
            countMTH = 0
            countSCI = 0
        # last row, append data
        else:
            mcasScore = (totalELA+totalMTH+totalSCI) / 3
            #mcasScore = normalizeScore((totalELA+totalMTH+totalSCI) / 3)
            if  district in data:
                data[district][7] = mcasScore
                currScore = float(data[district][-1])
                currScore += calculateWeightedScore(['MCAS', mcasScore])
                data[district][-1] = round(currScore, 2)
            else:
                print 'MCAS: Skipping ',district
                continue

    # SAT Score
    satData = pd.read_excel(dataLocation+fileName+ext, sheetname='SAT-District', header=0)
    
    for row in range(len(satData)):
        district = satData.iloc[row, 0]
        reading = satData.iloc[row, 2]
        writing = satData.iloc[row, 3]
        math = satData.iloc[row, 4]
        
        if np.isnan(reading) or np.isnan(writing) or np.isnan(math):
            satScore = 0
        else:
            satScore = calculateSATScore(reading+writing+math)
        
        if not district in data:
            print 'SAT: Skipping ',district
            continue
            
        data[district][8] = satScore
        currScore = float(data[district][-1])
        currScore += calculateWeightedScore(['SAT', satScore])
        data[district][-1] = round(currScore, 2)
  
#     # Teacher Salary Score
#     salaryData = pd.read_excel(dataLocation+fileName+ext, sheetname='Teacher-Salary', header=0)
# 
#     for row in range(len(salaryData)):
#         district = salaryData.iloc[row, 0]
#         salary = salaryData.iloc[row, 2]
#         # remove $ and , from value
#         salary = int(salary[1:].replace(',', '', 1))
#         if np.isnan(salary):
#             continue
#         salaryScore = calculateSalaryScore(salary)
#         
#         if district in data:
#             data[district][9] = salaryScore
#         else:
#             print 'Salary: Adding row for ',district
#             data[district] = ['', '', '', '', '', '', '', '', '', '']
#             data[district][9] = salaryScore  

    # School Rank Score
    rankData = pd.read_excel(dataLocation+fileName+ext, sheetname='Rank-District', header=0)
  
    for row in range(len(rankData)):
        district = str(rankData.iloc[row, 0])
        school_type = str(rankData.iloc[row, 1])
        rank = rankData.iloc[row, 2]
        grade = str(rankData.iloc[row, 3])
        
        if np.isnan(float(rank)):
            rankScore = 0
        else:
            rank = int(rank)
            rankScore = calculateRankScore(rank)
          
        if not district in data:
            print 'Rank: Skipping ',district
            continue
            
        data[district][9] = rankScore
        currScore = float(data[district][-1])
        currScore += calculateWeightedScore(['Rank', rankScore])
        data[district][-1] = round(currScore, 2)  
            
    df = pd.DataFrame.from_items(data.items(), columns=columns, orient='index')
    
    return df