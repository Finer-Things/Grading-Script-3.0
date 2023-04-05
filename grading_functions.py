import math

import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import seaborn as sns
import matplotlib.pyplot as plt






def letter_grade_assigner(row, final_condition = False, great_effort_rule = False, grade_column_name = "Grade", final_grade_column_name = "Final"):
    """
    This letter grade assigner takes a raw grade percentage and outputs a letter grade. There are two peculiarities to this function that are not in a standard letter grade assigner: 
    1) This course has a tradition of grading with a "Great Effort Rule" that assigns a B to students who earn a C or better through raw score if they took most of the quizzes, came to lecture and completed at least most of the homework. I took a quick look at the spreadsheet and did not find any students who fell into this category without having reasonably high homework and quiz scores, so I just applied this to everyone. 
    2) This was a tough quarter, and some students struggled all quarter with low grades and ended up doing a stellar job on the final. I believe that these students earned the grade they got on the final (especially because this was not a take-home exam, which would offer them the chance to get "helped" by someone else). So the students who received a higher percentage on the final than they did in the class were graded according to their final score. The great effort rule was not applied in this case, nor should it be. 
    Functionality: The variable num is used as a default for a letter grade assignment. You will see this not used in the case of being assigned B grades because the Great Effort Rule is based on their raw score. For the lines below, num could have been used instead of row["Final"] without change, but I think this could have easily muddied what was happening so I kept the "Final" argument. 
    """
    if final_condition:
        num = max(row[grade_column_name], row[final_grade_column_name])
    else: 
        num = row[grade_column_name]
    if num > 104:
        return "huh?"
    elif num >= 97:
        return "A+"
    elif num >= 92.5:
        return "A"
    elif num >= 90:
        return "A-"
    elif num >= 87:
        return "B+"
    elif great_effort_rule and row[grade_column_name] >= 72.5: #For Math 34A/B's "Great Effort Rule" - never based on higher final grade!
        return "B"
    elif num >= 82.5:
        return "B"
    elif num >= 80:
        return "B-"
    elif num >= 77:
        return "C+"
    elif num >= 72.5:
        return "C"
    elif num >= 70:
        return "C-"
    elif num >= 67:
        return "D+"
    elif num >= 62.5:
        return "D"
    elif num >= 60:
        return "D-"
    else: 
        return "F"


def missed_exam_replacer(row, list, exam_name, replacement_column_name):
    """
    This is a blanket function to be used in the df.apply() method, with row being the default entry in the df.apply() method. 
    list is a list of student ids for students who have excused absences for the column in question. 
    exam_name is the column name of your dataframe (because you want to return that value for everyone who didn't have an excused absence)
    replacement_column_name is the column name with the replacement grade value. 
    """
    if row["SID"] in list:
        return row[replacement_column_name]
    else:
        return row[exam_name]


def quiz_average_calculator(row, quiz_max_points, i):
    """
    The computes the total quiz score divided by the adjusted maximum points (see the description for quiz_tuple_function's, whose outputs are used as inputs for this function's computation). 
    """
    points_earned = sum([row["Quiz "+str(i)+"-"][0] for i in range (1,len(quiz_max_points)+1)])
    total_points = sum(quiz_max_points)-sum([row["Quiz "+str(i)+"-"][1] for i in range(1,len(quiz_max_points)+1)])
    #This part was used to look at some of the totals to make sure the function works as intended. 
    #if i < 20:
    #    print(points_earned, total_points, 100*points_earned/total_points)
    return np.round(100*points_earned/total_points, decimals=1)
                                            

def quiz_missing_points_allocator(row, quiz_max_points, i, excused_list, trevor_students):
    if row["SID"] in excused_list or (i in [4,6] and row["SID"] in trevor_students):
        return np.round(row["QT"]/100*quiz_max_points[i-1], decimals=1)
    else: 
        return row["Quiz "+str(i)]

    
def quiz_tuple_function(row, excused_list, trevor_students, i, quiz_max_points):
    """
    This is meant to help compute a fair quiz grade for students who were sick during a quiz. This is done by summing the first entry for the point total and subtracting the second entry from the maximum points possible in the denominator. More specifically, this function returns tuples with the student's quiz score followed by a 0 for most students' quizzes and a 0 followed by the quiz's maximum points if the student had an excused abscence. 
    """
    if row["SID"] in excused_list or (i in [4,6] and row["SID"] in trevor_students):
        return (0,quiz_max_points[i - 1])
    else: 
        return (row["Quiz "+str(i)],0) 

    
    
    
def version_merger(row, version_list):   # row is a Series
    """
    This takes in a dataframe row and returns the entry from the version list with the first value, or nan if none of the entries have values. The inputs are "row" to be used by the dataframe operation (with a lambda function and the .apply method) and the version list is meant to tell the .apply method which column titles to look for. 
    """
    for item in version_list:
        if not np.isnan(row[item]):
            return row[item]
    return np.nan
 





