import math
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
import requests
import os
import sys     




class Course:
    all_courses = []
    def __init__(self, name = None, quarter = None, id_format = "netID", grade_categories = [], spreadsheets = []):
        self.name = name
        self.quarter = quarter
        self.grade_categories = grade_categories
        self.spreadsheets = spreadsheets
        self.id_format = id_format #Either "netID" or "Perm #"
        if self.id_format not in ["netID", "Perm #"]:
            raise Exception('The attribute id_format must be either "netID" or "Perm #".')
        Course.all_courses.append(self)
        self.main_spreadsheet = None # Spreadsheet class for computing totals that will be created later
        self.roster = []

        # Make Directory -- I couldn't get this to work with the master directory for the file
        # path = r'C:\Users\natha\Python Stuff\Administration, Grading, etc for Teaching'
        # sys.path.append(path)
        # if self.quarter != None:
        #     quarter_folder_name = f"{self.quarter[-2:]} {self.quarter[0]}"
        #     if not os.path.exists(quarter_folder_name):
        #         os.mkdir(quarter_folder_name)
        #     if self.name != None:
        #         course_folder_name = self.name
        #         if not os.path.exists(course_folder_name):
        #             os.mkdir(course_folder_name)


    def __str__(self):
        return f"{self.quarter} {self.name}"
    
    def create_master_spreadsheet(self):
        self.master_spreadsheet = MasterSpreadsheet(self)
        ### Step 1: Merging the spreadsheets
        # Gradescope Spreadsheet Integration
        gradescope_spreadsheet_list = [spreadsheet for spreadsheet in self.spreadsheets if spreadsheet.source == "Gradescope"]
        if gradescope_spreadsheet_list != []:
            gradescope_spreadsheet = gradescope_spreadsheet_list[0]
            self.master_spreadsheet.max_points_hash = gradescope_spreadsheet.max_points_hash
                        
            # Egrades Spreadsheet Integration
            egrades_spreadsheet_list = [spreadsheet for spreadsheet in self.spreadsheets if spreadsheet.source == "Egrades"]
            if egrades_spreadsheet_list != []:
                egrades_spreadsheet = egrades_spreadsheet_list[0]
                egrades_spreadsheet.df = egrades_spreadsheet.df[['Enrl Cd', 'netID', 'Perm #', "Letter Grade Submitted", 'Email', 'ClassLevel', 'Major1', 'Major2']]
                self.master_spreadsheet.df = pd.merge(gradescope_spreadsheet.df, egrades_spreadsheet.df, on=self.id_format, how ="right")
            # Webwork Spreadsheet Integration
            webwork_spreadsheet_list = [spreadsheet for spreadsheet in self.spreadsheets if spreadsheet.source == "Webwork"]
            if webwork_spreadsheet_list != []:
                webwork_spreadsheet = webwork_spreadsheet_list[0]
                #### Note that this may not work yet because we haven't found the column name associated with self.id_format (or even set it!) for the webwork spreadsheet class
                self.master_spreadsheet.df = pd.merge(self.master_spreadsheet.df, webwork_spreadsheet.df, on=self.id_format, how ="left")
                self.master_spreadsheet.max_points_hash = self.master_spreadsheet.max_points_hash | webwork_spreadsheet.max_points_hash
        
            # Adding all of the columns that match each grade category
            for grade_category in self.grade_categories:
                grade_category.spreadsheet_to_grade_items_hash[self.master_spreadsheet.source] = [column for column in self.master_spreadsheet.df.columns if grade_category.name in column]
        
        ### Step 2: Instantiating/updating students from the rows of the new dataframe
        # Definition of the function to be applied below. For each row, the student info will either instantiate a new student or add the student's course info to the course. 
        def get_student_info_from_row(row):
            if row["netID"] in Student.lookup_by_netID:
                student = Student.lookup_by_netID[row["netID"]]
                student.courses.append(self)
            else:
                student = Student(row["netID"], row["First Name"], row["Last Name"], self, row["Perm #"])

            if "math" in str(row["Major1"]).lower() or "math" in str(row["Major2"]).lower():
                self.math_majors.append(student)
            return student
        
        self.math_majors = []
        self.master_spreadsheet.df["Student List"] = self.master_spreadsheet.df.apply(get_student_info_from_row, axis=1)
        self.roster.sort(key = lambda student: student.first_name)
        
        ### Step 3: Setting the Grade Category Columns, Computing their totals, and computing grades/assigning letter grades. THIS SHOULD BE BROKEN UP IN THE FUTURE SO CURVING CAN HAPPEN!
        # Computing Category Totals
        # grade_category.spreadsheet_to_grade_items_hash[self.master_spreadsheet.source] = [column for column in self.master_spreadsheet.df.columns if grade_category.name in column]
        for grade_category in self.grade_categories:
            if grade_category.assignment_weighting == "equal":
                for grade_cat_col_name in grade_category.spreadsheet_to_grade_items_hash[self.master_spreadsheet.source]:
                    self.master_spreadsheet.df[grade_cat_col_name] *= 100/self.master_spreadsheet.max_points_hash[grade_cat_col_name]
                    self.master_spreadsheet.max_points_hash[grade_cat_col_name] = 100

            # This control flow ensures empty categories have a zero total. When grade columns are created, these will not be factored into grade calculations. 
            grade_items = grade_category.spreadsheet_to_grade_items_hash[self.master_spreadsheet.source]
            if len(grade_items) < grade_category.number_of_dropped_assignments:
                raise Exception(f"You have {len(grade_items)} grade items under the {grade_category} grading category and {grade_category.number_of_dropped_assignments} drop. You cannot drop more assignments than you have!")
            if len(grade_items) > 0:
                drop_num = grade_category.number_of_dropped_assignments
                self.master_spreadsheet.df[f"{grade_category.name} Total"] = self.master_spreadsheet.df[grade_items].apply(lambda row: sum(sorted(row.fillna(0))[drop_num:]), axis=1)
                self.master_spreadsheet.max_points_hash[f"{grade_category.name} Total"] = sum(sorted([self.master_spreadsheet.max_points_hash[item] for item in grade_items])[drop_num:])
                
                # Normalizing the Totals
                self.master_spreadsheet.df[f"{grade_category.name} Total"] *= 100/self.master_spreadsheet.max_points_hash[f"{grade_category.name} Total"]
                self.master_spreadsheet.max_points_hash[f"{grade_category} Total"] = 100
                #Rounding to Two Decimal Places
                self.master_spreadsheet.df[f"{grade_category.name} Total"] = self.master_spreadsheet.df[f"{grade_category.name} Total"].apply(np.round, decimals=2)
            else:
                self.master_spreadsheet.df[f"{grade_category.name} Total"] = 0
        # Computing grades and assigning letter grades
        #
    
    def create_pie_chart(self, renaming_dictionary = {}):
        # Making sure there's an images folder
        if not os.path.exists("Images"):
            os.mkdir("Images")
        
        # Completing the naming dictionary from the renaming dictionary
        naming_dictionary = {category.name:category.name for category in self.grade_categories} | renaming_dictionary
        
        #Pie Chart
        grade_items_list = [naming_dictionary[category.name] for category in self.grade_categories]
        grade_item_percentages = [category.percent_weight for category in self.grade_categories]
        #plt.pie(grade_item_percentages, labels = grade_items_list, autopct='%0.1f%%')
        explode = [.05,.05,.05,.05, .05] # To slice the perticuler section
        colors = ["blue", "darkorange", "forestgreen", "purple",'g', "b"][:len(self.grade_categories)] # Color of each section
        textprops = {"fontsize":30} # Font size of text in pie chart

        fig1, ax1 = plt.subplots()
        with plt.style.context("seaborn-paper"):
            a,b,m = ax1.pie(grade_item_percentages, 
                            labels = grade_items_list, 
                            radius = 2, 
                            explode=None, 
                            # colors=colors, 
                            autopct='%.0f%%', 
                            textprops=textprops)
            [m[i].set_color('white') for i in range(len(m))]

        plt.savefig(f"Images/{self.quarter} {self.name} Grade Category Pie Chart.png", bbox_inches = "tight")
        plt.show()
        plt.close()

    def print_student_grade_breakdown(self, student_name, position = None, use_last_name = False):
        if use_last_name == True:
            first_or_last_name = "Last Name"
        else:
            first_or_last_name = "First Name"
        display_list = ["First Name", "Last Name", "Grade"]+[grade_category+" Total" for grade_category in self.grade_item_categories]+["Letter Grade"]
        print_dataframe = self.grades[self.grades[first_or_last_name].apply(lambda entry: student_name.lower() in entry.lower())][display_list]
        if position == None:
            for category in display_list:
                print(f"{str(category)[:10]:13}|", end="")
            print("")
            for row in print_dataframe.itertuples():
                for index, category in enumerate(display_list):
                    print(f"{str(row[index+1])[:13]:13}|", end="")
                print("")
        else:
            print_list = print_dataframe.iloc[position]
            for item in display_list:
                print(f"{str(item)[:13]:13}|", end="")
            print("")
            for item in print_list:
                print(f"{str(item)[:10]:13}|", end="")
            print("")
    
    







class GradeCategory:
    """Example Instantiation: homework = GradeCategory("Homework", 20, 1, "standard")
    Note that this will actually have an equal assignment weighting, not standard, because the number of assignments to drop is > 0."""
    def __init__(self, name = None, course = None, percent_weight = 0, number_of_dropped_assignments = 0, assignment_weighting = "standard"):
        self.name = name
        self.course = course
        self.percent_weight = percent_weight
        self.assignment_weighting = assignment_weighting
        self.number_of_dropped_assignments = number_of_dropped_assignments
        self.spreadsheet_to_grade_items_hash = {}
        
        # Adding the category to the course
        if isinstance(self.course, Course):
            self.course.grade_categories.append(self)
        
        # Making the assignment weightings equal if any assignments are dropped
        if self.number_of_dropped_assignments > 0:
            self.assignment_weighting = "equal"
        
        # Raise Exception if we don't have a valid assignment weighting for the category
        if self.assignment_weighting not in ["standard", "equal"]:
            raise Exception('The attritube assignment_weighting must be either "standard" or "equal".')
        

    def __str__(self):
        return f"Grade category {self.name} for {self.course}"
    
    def describe(self):
        return f"{self.name} is a grade category for {self.course}. \n" + \
                f"It's worth {self.percent_weight}% of the course grade and the lowest {self.number_of_dropped_assignments} grade items will be dropped. \n" + \
                f"Its assignments have a(n) {self.assignment_weighting} weighting when the total is calculated."


class Spreadsheet:
    """
    Notes: 
       1) course attribute must be an instance of the Course class
       2) if the associated course has an id format already, it will be set automatically for the spreadsheet as well. 
    """
    def __init__(self, course = None, file_name = None, df = None, id_format = None, id_column_name = None):
        self.course = course
        self.file_name = file_name
        self.df = df
        self.id_format = id_format
        self.id_column_name = id_column_name
        self.source = None
        # Adding this spreadsheet to the spreadsheet list for its course and inheriting the id_format from the course (if either is possible)
        if isinstance(self.course, Course):
            self.course.spreadsheets.append(self)
            if self.course.id_format != None:
                self.id_format = self.course.id_format 
        
        if self.file_name != None:
            self.df = pd.read_csv(self.file_name)

class GradescopeSpreadsheet(Spreadsheet):
    def __init__(self, course = None, file_name = None, df = None, id_format = None, id_column_name = "SID"):
        super().__init__(course, file_name, df, id_format, id_column_name)
        self.source = "Gradescope"
        # More Stuff particular to Gradescope Spreadsheet like the max columns becoming an attribute and then deleting the junk columns
        # self.id_column_name = "SID" #Because SID is always used to indicate whatever Canvas or Gauchospace is using, whether perm or netID
        if isinstance(self.df, pd.DataFrame):
            self.set_max_points_info()
            self.drop_junk_columns()
        else:
            print(f"Gradescope Spreadsheet {self} instantiated with no dataframe.")
        
        # Renaming the SID ("Student ID") column to course.id_format name. That way it's "netID" for Canvas and "Perm #" for Gauchospace
        self.df.rename(columns = {"SID": self.course.id_format}, inplace = True)

        # Adding all of the columns that match each grade category
        for grade_category in self.course.grade_categories:
            grade_category.spreadsheet_to_grade_items_hash[self.source] = [column for column in self.df.columns if grade_category.name in column]
    
    def __str__(self):
        return f"Gradescope Spreadsheet for {self.course}"
    
    def set_max_points_info(self):
        """Creates a Dictionary for Max Points"""
        max_points_column_names = [name for name in self.df.columns if "Max Points" in name]
        part_to_chop = len(" - Max Points")
        self.max_points_hash = {name[:-part_to_chop]: self.df[name].iloc[1] for name in max_points_column_names}
    
    def drop_junk_columns(self):
        junk_column_indices = [i for i, column in enumerate(self.df.columns) \
                       if "Max Points" in column or "Submission Time" in column \
                       or "Lateness" in column or column == "section_name" \
                       or column == "Email"
                       ]
        self.df.drop(self.df.columns[junk_column_indices], axis=1, inplace=True)

class EgradesSpreadsheet(Spreadsheet):
    def __init__(self, course = None, file_name = None, df = None, id_format = None, id_column_name = None):
        super().__init__(course, file_name, df, id_format, id_column_name)
        self.source = "Egrades"
        self.df.rename(columns = {"Grade": "Letter Grade Submitted"}, inplace = True)
        self.df["netID"] = self.df["Email"].apply(lambda entry: entry.split("@")[0])

class WebworkSpreadsheet(Spreadsheet):
    def __init__(self, course = None, file_name = None, df = None, id_format = None):
        super().__init__(course, file_name, df, id_format, id_column_name)
        self.source = "Webwork"
        """
        Still left to do: 
        1) Identify the id column (based on its course's id_format) and, in the case of netID, create a new SID column with the first several letters of their emails addresses
        2) Figure out format, stripping/cleaning the spaces out of the columns and column names, identifying the homework total column
        3) If we want to take a look at individual assignments, creating a max_points_hash attribute to track the maximum points for each assignment
        """
        self.max_points_hash = {"Homework": 100}
        # If either of the lines below throw an error, it's because the column names aren't matching
        webwork_total_col_name = [col_name for col_name in self.df.columns if r"%score" in col_name][0]
        id_col_name = [col_name for col_name in self.df.columns if "login ID" in col_name][0]
        self.df.rename(columns = {webwork_total_col_name: "Homework", id_col_name: self.id_format}, inplace = True)

        # Adding all of the columns that match each grade category
        for grade_category in self.course.grade_categories:
            grade_category.spreadsheet_to_grade_items_hash[self.source] = [column for column in self.df.columns if grade_category.name in column]

class MasterSpreadsheet(Spreadsheet):
    def __init__(self, course = None, file_name = None, df = None, id_format = None, id_column_name = "SID"):
        super().__init__(course, file_name, df, id_format, id_column_name)
        self.source = "Master"



class GradeCalculator:
    def __init__(self, course):
        self.course = course
    
    def compute_standard_grades(self, main_spreadsheet = None):
        if main_spreadsheet == None:
            main_spreadsheet = self.course.main_spreadsheet


class Student:
    # Hash Table of all students based on netID
    lookup_by_netID = {}
    # Hash Table of all students based on perm_number
    lookup_by_perm = {}
    def __init__(self, netID, first_name = None, last_name = None, course = None, perm_number = None):
        self.netID = netID
        self.first_name = first_name
        self.last_name = last_name
        self.perm_number = perm_number
        # course is NOT used as an attribute, but rather as a launching point 
        if isinstance(course, Course):
            self.courses = [course]
        Student.lookup_by_netID[self.netID] = self
        Student.lookup_by_perm[self.perm_number] = self
        self.courses[0].roster.append(self)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.netID}"
        









############################# Functions ##################################

def letter_grade_assigner(row, final_condition = None, great_effort_rule = False, grade_column_name = "Grade", final_grade_column_name = "Final Total"):
        """
        This letter grade assigner takes a raw grade percentage and outputs a letter grade. There are two peculiarities to this function that are not in a standard letter grade assigner: 
        1) Math 34A/B have a tradition of grading with a "Great Effort Rule" that assigns a B to students who earn a C or better through raw score if they took most of the quizzes, came to lecture and completed at 
        least most of the homework. I took a quick look at the spreadsheet and did not find any students who fell into this category without having reasonably high homework and quiz scores, so I just applied this to 
        everyone. 
        2) This was a tough quarter, and some students struggled all quarter with low grades and ended up doing a stellar job on the final. I believe that these students earned the grade they got on the final 
        (especially because this was not a take-home exam, which would offer them the chance to get "helped" by someone else). So the students who received a higher percentage on the final than they did in the class 
        were graded according to their final score. The great effort rule was not applied in this case, nor should it be. 
        Functionality: The variable num is used as a default for a letter grade assignment. You will see this not used in the case of being assigned B grades because the Great Effort Rule is based on their raw score. For the lines below, num could have been used instead of row["Final"] without change, but I think this could have easily muddied what was happening so I kept the "Final" argument. 
        """
        if final_condition == None:
            final_condition = self.final_condition
        
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


