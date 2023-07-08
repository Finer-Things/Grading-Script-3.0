import math
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
import requests
import os
import sys

path = r'C:/Users/natha/Python Stuff/Grading Script 3.0'
sys.path.append(path)
from Course_Class import *
from grading_functions import *





# Course
math_course = Course("Math 4B", "Spring 2023", "Perm #")

# Grade Categories
midterm = GradeCategory(name = "Midterm", 
                        percent_weight = 40, 
                        number_of_dropped_assignments = 0, 
                        assignment_weighting = "equal"
                       )
quiz = GradeCategory("Quiz", 10, 1)
homework = GradeCategory("Homework", 20)
final = GradeCategory("Final", 30, 1)

# Medical Miss Setup:
## Creating a dictionary for students who have medically excused grade items by category
mm_df = pd.read_csv("data/Medical Miss Roster (Complete).csv")
midterm.medical_miss_dict = pd.Series(mm_df["Medical Miss Midterms"].fillna(0).astype(int).values,index = mm_df["Perm #"]).to_dict()
## The Quiz Dictionary has to be different because we are dropping a quiz grade already. 
def drop_by_one(value: int) -> int:
    if value == 0:
        return value
    elif value >= 0:
        return value - 1
    else: 
        raise Exception("Entry must be 0 or greater.")

mm_df["Medical Miss Quizzes"] = mm_df["Medical Miss Quizzes"].fillna(0).astype(int).apply(drop_by_one)
quiz.medical_miss_dict = pd.Series(mm_df["Medical Miss Quizzes"].values,index = mm_df["Perm #"]).to_dict()

# Grade Spreadsheets, once they're available
path_to_spreadsheet_files = "data/"
gradescope_spreadsheet = GradescopeSpreadsheet(path_to_spreadsheet_files + "Math_4B_Spring_2023_grades.csv")
egrades_spreadsheet = EgradesSpreadsheet(path_to_spreadsheet_files + "S23_MATH4B_29421All.csv")
webwork_spreadsheet = WebworkSpreadsheet(path_to_spreadsheet_files + "Math_4B_Webwork_Totals.csv", id_format = "NetID", id_column_name = "login ID", eleven_percent_extra_credit = True)

# Master Spreadsheet
math_course.create_master_spreadsheet()

# Empty Grade Category Warning
empty_cats = [cat for cat in math_course.grade_categories if len(cat.grade_items) == 0]
if len(empty_cats) > 0:
    print(f"Categories that still have no grade item: ", *empty_cats)


# Create Egrades File
math_course.create_egrades_file()