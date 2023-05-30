import math
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt


from Course_Class import *
from grading_functions import *


# Course
math_4B = Course("Math 4B", "Spring 2023", "Perm #")

# Grade Categories
midterm = GradeCategory(name = "Midterm", 
                        percent_weight = 40, 
                        number_of_dropped_assignments = 0
                       )
quiz = GradeCategory("Quiz", 10)
homework = GradeCategory("Homework", 20)
final = GradeCategory("Final", 30)

# Grade Spreadsheets, once they're available
gradescope_spreadsheet = GradescopeSpreadsheet("../Administration, Grading, etc for Teaching/23S Grades/Math 4B/Math_4B_Spring_2023_grades.csv")

# df = pd.read_csv("../Administration, Grading, etc for Teaching/23S Grades/Math 4B/Math_4B_Spring_2023_grades.csv")
# print(df.head())
print(gradescope_spreadsheet.df.head())