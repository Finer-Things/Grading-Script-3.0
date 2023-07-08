import math
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
import time
import requests
import os
import sys     

path = r'C:\Users\natha\Python Stuff\Grading Script 3.0'
sys.path.append(path)


from Course_Class import *
from grading_functions import *


########## Course Setup for Math 108A ###########
# Course
math_108A = Course("Math 108A", "Winter 2023", "netID")
course = math_108A

# Grade Categories
midterm = GradeCategory("Midterm", course, 30)
homework = GradeCategory(name = "Homework", 
                         course = course, 
                         percent_weight = 30, 
                         number_of_dropped_assignments = 0, 
                         assignment_weighting = "equal"
                        )
final = GradeCategory("Final", course, 40, 0)

# Grade Spreadsheets, once they're available
gradescope_spreadsheet = GradescopeSpreadsheet(course, "../Administration, Grading, etc for Teaching/23W Grades/Math 108A/Math_108A_Winter_2023_grades.csv")
egrades_spreadsheet = EgradesSpreadsheet(course, "../Administration, Grading, etc for Teaching/23W Grades/Math 108A/W23_MATH108A_31583All.csv")


########## Setting up the Curves ###########
# Custom Curving Function for the Midterm curve
def midterm_grading_function(row):
    # It was important to fill NaN values because these caused errors when I first tried to implement this curve
    row = row.fillna(0)
    # Applying makeup points: 30% toward a score of 55 for each reflection completed
    new_score =  row["Midterm"] + (55-row["Midterm"])*(row["Reflection: Mid-term"] + row["Reflection: Definitions"])/100*.3
    # Making the midterm out of 50 instead of 52
    # This seemed easier than trying to manually reset the max points from 52 to 50. 
    new_score *= 52/50
    return new_score

midterm_curve = CurveSetter(None, 
                            "Midterm", 
                            course, 
                            "Custom", 
                            None, 
                            False, 
                            midterm_grading_function
                           )

final_curve = CurveSetter(96, 
                            final, 
                            course, 
                            "New Ceiling"
                           )

homework_curve = CurveSetter(78, 
                            homework, 
                            course
                           )


########## Merging the Spreadsheets and Compiling Grades, etc. ###########
course.create_master_spreadsheet()


########## Plot a Grade Item ###############
# course.plot_grade_item("Final Exam", 3)


##########
student = math_108A.roster[18]
# math_108A.create_pie_chart({}, 0)
# time.sleep(4)
student.create_pie_chart(math_108A)
