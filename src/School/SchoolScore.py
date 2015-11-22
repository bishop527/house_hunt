'''
Created on Nov 17, 2015

@author: ad23883
'''
import pandas as pd
import numpy as np

maxScore = 10
minScore = -10
medianScore = 0

dataLocation = 'data/school/'
fileName = 'Master-School_Data-2015'
ext = '.xlsx'
    
def normalizeScore(score):
        # Restrict score to no greater then maxScore and no less then minScore
    if score > maxScore:
        score = maxScore
    elif score < minScore:
        score = minScore
    return score

def calculateAccountabilityScore(value):
    score = 0
    
    if value == 'Level 4':
        score = -10
    elif value == 'Level 3':
        score = -5
    elif value == 'Level 2':
        score = 5
    elif value == 'Level 1':
        score = 10
    # level most likely set to insufficient data. Score as 0 so doesn't help nor harm
    else:
        score = 0
    
    return normalizeScore(score)
    
def calculateClassSizeScore(value):
    score = 0
    minValue = 10
    maxValue = 30
    medianValue = (maxValue+minValue)/2

    step = int((maxValue-minValue)/10)    
    score = int((medianValue - round(value))/step)*2 
     
    return normalizeScore(score)

def calculateSPEDPercScore(value):
    score = 0
    minValue = 8.0
    maxValue = 24.0
    medianValue = (maxValue+minValue)/2

    step = ((maxValue-minValue)/10)    
    score = int((medianValue - round(value))/step)*2 
     
    return normalizeScore(score)

def calculateDropoutScore(value):
    score = 0
    minValue = 0.0
    maxValue = 5.0
    medianValue = (maxValue+minValue)/2
    
    step = (maxValue-minValue)/10    
    score = int((medianValue - round(value))/step)*2 
    
    return normalizeScore(score)

def calculateGraduationScore(value):
    score = 0
    minValue = 86.0
    maxValue = 100
    medianValue = (maxValue+minValue)/2
    
    step = (maxValue-minValue)/10    
    score = int((round(value) - medianValue)/step)*2 
    
    return normalizeScore(score)

def calculateHigherEdScore(value):
    score = 0
    minValue = 60.0
    maxValue = 100
    medianValue = (maxValue+minValue)/2

    step = (maxValue-minValue)/10    
    score = int((round(value) - medianValue)/step)*2 
    
    return normalizeScore(score)

def calculateMCASScore(category, value):

    if category == 'Prof_Adv':
        minValue = 20
        maxValue = 80
    elif category == 'NI' or category == 'W/F':
        minValue = 10
        maxValue = 0
    
    medianValue = (maxValue+minValue)/2
    
    if category == 'Prof_Adv': 
        step = int(maxValue-minValue)/10    
        score = int((round(value) - medianValue)/step)*2 
    else:
        step = int(minValue-maxValue)/10    
        score = int((medianValue-round(value))/step)*2 
    
    return normalizeScore(score)

def calculateSATScore(value):
    score = 0
    minValue = 1000
    maxValue = 2000
    medianValue = (maxValue+minValue)/2
    
    step = int(maxValue-minValue)/10    
    score = int((round(value) - medianValue)/step)*2 
    
    return normalizeScore(score)

def calculateParentInvolveScore(value):
    minValue = 50
    maxValue = 100
    medianValue = (maxValue+minValue)/2

    step = (maxValue-minValue)/10    
    score = int((round(value) - medianValue)/step)*2 
    
    return normalizeScore(score)

def calculateSalaryScore(value):
    minValue = 50000
    maxValue = 90000
    medianValue = (maxValue+minValue)/2

    step = (maxValue-minValue)/10    
    score = int((round(value) - medianValue)/step)*2 
    
    return normalizeScore(score)

def calculateRankScore(value):
    minValue = 250
    maxValue = 1
    medianValue = (maxValue+minValue)/2

    step = (minValue-maxValue)/10    
    score = int((medianValue-round(value))/step)*2 
    
    return normalizeScore(score)

def calculateSchoolScores():
    print 'Calculating School Scores'
    
    score = 0
    data = {}
    columns = ['Accnt Level ', 'Class Size', 'Parent Involve', 'SPED %', 'Dropout %', 'Grad %', 'HigherEd %', 'MCAS', 'SAT', 'School Rank']
        
    # Accountability Level Score
    accntData = pd.read_excel(dataLocation+fileName+ext, sheetname='Accountability-District', header=0)    
    for row in range(len(accntData)):
        district = accntData.iloc[row, 0]
        level = accntData.iloc[row, 1]
        accntScore = calculateAccountabilityScore(level)
        
        if district in data:
            data[district][0] = accntScore
        else:
            data[district] = ['', '', '', '', '', '', '', '', '', '']
            data[district][0] = accntScore
    
    # Class Size and SPED % Score
    classSizeData = pd.read_excel(dataLocation+fileName+ext, sheetname='Class_Size-District', header=0)
    
    # Class Size
    for row in range(len(classSizeData)):
        district = classSizeData.iloc[row, 0]
        classSize = classSizeData.iloc[row, 1]
        if np.isnan(classSize):
            continue
        classSizeScore = calculateClassSizeScore(classSize)
        
        if district in data:
            data[district][1] = classSizeScore
        else:
            print 'ClassSize: Adding row for ',district
            data[district] = ['', '', '', '', '', '', '', '', '', '']
            data[district][1] = classSizeScore
        
    # SPED %
    for row in range(len(classSizeData)):
        district = classSizeData.iloc[row, 0]
        spedPerc = classSizeData.iloc[row, 2]
        if np.isnan(spedPerc):
            continue
        spedPercScore = calculateSPEDPercScore(spedPerc)
        
        if district in data:
            data[district][3] = spedPercScore
        else:
            print 'SPED %: Adding row for ',district
            data[district] = ['', '', '', '', '', '', '', '', '', '']
            data[district][3] = spedPercScore
    
    # SPED Parent Involvement Score
    parentData = pd.read_excel(dataLocation+fileName+ext, sheetname='SPED-Performance', header=0, skiprows=2)
    
    for row in range(len(parentData)):
        district = parentData.iloc[row, 1]
        parentPerc = parentData.iloc[row, 13]
        if parentPerc == 'NR' or parentPerc == '-':
            continue
        parentPerc = float(parentPerc)
        if np.isnan(parentPerc):
            continue
        parentScore = calculateParentInvolveScore(parentPerc)
        
        if district in data:
            data[district][2] = parentScore
        else:
            print 'Parent: Adding row for ',district
            data[district] = ['', '', '', '', '', '', '', '', '', '']
            data[district][2] = parentScore
            
    # Dropout Rate Score
    dropoutData = pd.read_excel(dataLocation+fileName+ext, sheetname='Dropout-District', header=0)
    
    for row in range(len(dropoutData)):
        district = dropoutData.iloc[row, 0]
        dropPerc = dropoutData.iloc[row, 3]
        if np.isnan(dropPerc):
            continue
        dropoutScore = calculateDropoutScore(dropPerc)
        
        if district in data:
            data[district][4] = dropoutScore
        else:
            print 'Dropout: Adding row for ',district
            data[district] = ['', '', '', '', '', '', '', '', '', '']
            data[district][4] = dropoutScore

    # Graduation Rate Score
    graduationData = pd.read_excel(dataLocation+fileName+ext, sheetname='GraduationRates-District', header=0)
    
    for row in range(len(graduationData)):
        district = graduationData.iloc[row, 0]
        gradPerc = graduationData.iloc[row, 2]
        if np.isnan(gradPerc):
            continue
        gradScore = calculateGraduationScore(gradPerc)
    
        if district in data:
            data[district][5] = gradScore
        else:
            print 'Grad: Adding row for ',district
            data[district] = ['', '', '', '', '', '', '', '', '', '']
            data[district][5] = gradScore

    # Higher Education Rate Score
    higherEdData = pd.read_excel(dataLocation+fileName+ext, sheetname='HigherEd-District', header=0)
    
    for row in range(len(higherEdData)):
        district = higherEdData.iloc[row, 0]
        higherEdPerc = higherEdData.iloc[row, 3]
        if np.isnan(higherEdPerc):
            continue
        higherEdScore = calculateHigherEdScore(higherEdPerc)
        
        if district in data:
            data[district][6] = higherEdScore
        else:
            print 'HigherEd: Adding row for ',district
            data[district] = ['', '', '', '', '', '', '', '', '', '']
            data[district][6] = higherEdScore

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
        if np.isnan(prof_advValue):
            continue
        prof_advScore = calculateMCASScore('Prof_Adv', prof_advValue)
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
        if np.isnan(niValue):
            continue
        niScore = calculateMCASScore('NI', niValue)
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
        if np.isnan(wfValue):
            continue
        wfScore = calculateMCASScore('W/F', wfValue)
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
            if mcasData.iloc[row+1, 0] != district:
                mcasScore = normalizeScore((totalELA+totalMTH+totalSCI) / 3)
                if district in data:
                    data[district][7] = mcasScore
                else:
                    print 'MCAS: Adding row for ',district
                    data[district] = ['', '', '', '', '', '', '', '', '', '']
                    data[district][7] = mcasScore
                
                totalELA = 0
                totalMTH = 0
                totalSCI = 0
                countELA = 0
                countMTH = 0
                countSCI = 0
        # last row, append data
        else:
            mcasScore = normalizeScore((totalELA+totalMTH+totalSCI) / 3)
            if district in data:
                data[district][7] = mcasScore
            else:
                print 'MCAS: Adding row for ',district
                data[district] = ['', '', '', '', '', '', '', '', '', '']
                data[district][7] = mcasScore
            
            totalELA = 0
            totalMTH = 0
            totalSCI = 0
            countELA = 0
            countMTH = 0
            countSCI = 0

    # SAT Score
    satData = pd.read_excel(dataLocation+fileName+ext, sheetname='SAT-District', header=0)
    
    for row in range(len(satData)):
        district = satData.iloc[row, 0]
        reading = satData.iloc[row, 2]
        writing = satData.iloc[row, 3]
        math = satData.iloc[row, 4]
        
        if np.isnan(reading) or np.isnan(writing) or np.isnan(math):
            continue
        
        satScore = calculateSATScore(reading+writing+math)
        
        if district in data:
            data[district][8] = satScore
        else:
            print 'SAT: Adding row for ',district
            data[district] = ['', '', '', '', '', '', '', '', '', '']
            data[district][8] = satScore
  
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
          
        if district in data:
            data[district][9] = rankScore
        else:
            print 'Rank: Adding row for ',district
            data[district] = ['', '', '', '', '', '', '', '', '', '']
            data[district][9] = rankScore  
            
    df = pd.DataFrame.from_items(data.items(), columns=columns, orient='index')
    writer = pd.ExcelWriter('Master_Scores-2015.xlsx')
    df.to_excel(writer,"School-Scores")
    writer.save()