import math
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import time
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
        self.master_spreadsheet = None # Spreadsheet class for computing totals that will be created later
        self.roster = []
        self.curve_setter_list = []

        """
        Make Directory
        The vision meant to be completed with this code was to create a folder for both the quarter and the course inside the Administrative folder. 
        That way if I'm just working in a notebook file and I point to the spreadsheets for a course, everything including the spreadsheet for Egrades
        can be generated as well as the folders. 
        It was a cool idea, but...
        I couldn't get the code below to work with the master directory we needed at the beginning of each notebook file to point to these classes. 
        It was just creating all the folders inside the same folder as the notebook file. So I used the code to create an Images folder 
        for the visualizations and that's it. 
        """
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
    
    def create_grade_columns(self, great_effort_rule = None, final_condition = None):
        """Used in the create_master_spreadsheet method to calculate the grade percentage as well as the letter grade.
        This method uses the letter_grade_assigner grading function."""
        # Great Effort Rule Check
        if hasattr(self, "great_effort_rule"):
            great_effort_rule = self.great_effort_rule
        elif great_effort_rule == None: 
            great_effort_rule = False
        
        # Final Condition Check
        if hasattr(self, "final_condition"):
            final_condition = self.final_condition
        elif final_condition == False:
            final_condition = False
        
        df = self.master_spreadsheet.df
        def grade_calculator(row):
            weighted_average_numerator = sum([row[category.name + " Total"]*category.percent_weight for category in self.grade_categories])
            weighted_average_denominator = sum([category.percent_weight for category in self.grade_categories if category.spreadsheet_to_grade_items_hash[self.master_spreadsheet.source] != [] ])
            """In the weighted average denominator above, note the condition at the end of the list grade items for each category needs to be non-empty in order for that category's
            percent weight to be counted in the computation. This means that rather than missing 30% of your grade because you haven't taken the final yet, instead you would just 
            see your grade without the final being considered, your 'before-the-final' grade."""
            # None is returned if there are no assignments found in any category. 
            if weighted_average_denominator == 0:
                first_name = row["First Name"]
                raise Exception(f"The student {first_name} has no recorded assignments recorded in any grading category.")
            return np.round(weighted_average_numerator/weighted_average_denominator, decimals=2)
            
        # Compute a grade percentage by applying the grade_calculator function above
        df["Grade"] = df.apply(grade_calculator , axis=1)
        
        """Checking the course for great effort rule and final_condition attributes before using them to compute letter grades. 
        They can also be fed into the create_grade_columns method directly."""
        # Great Effort Rule Check
        if hasattr(self, "great_effort_rule"):
            great_effort_rule = self.great_effort_rule
        elif great_effort_rule == None: 
            great_effort_rule = False
        
        # Final Condition Check
        if hasattr(self, "final_condition"):
            final_condition = self.final_condition
        elif final_condition == False:
            final_condition = False
        df["Letter Grade"] = df.apply(lambda row: letter_grade_assigner(row, final_condition, 
                                                                        great_effort_rule, 
                                                                        final_grade_column_name = [column_name for column_name in df.columns if "final" in column_name.lower()][0]
                                                                        ), 
                                      axis=1)
        

    def create_master_spreadsheet(self):
        self.master_spreadsheet = MasterSpreadsheet(self)
        ### Step 1: Merging the spreadsheets
        # Gradescope Spreadsheet Integration
        gradescope_spreadsheet_list = [spreadsheet for spreadsheet in self.spreadsheets if spreadsheet.source == "Gradescope"]
        if gradescope_spreadsheet_list != []:
            gradescope_spreadsheet = gradescope_spreadsheet_list[0]
            self.master_spreadsheet.max_points_hash = gradescope_spreadsheet.max_points_hash
            self.master_spreadsheet.df = gradescope_spreadsheet.df
                        
            # Egrades Spreadsheet Integration
            egrades_spreadsheet_list = [spreadsheet for spreadsheet in self.spreadsheets if spreadsheet.source == "Egrades"]
            if egrades_spreadsheet_list != []:
                egrades_spreadsheet = egrades_spreadsheet_list[0]
                egrades_spreadsheet.df = egrades_spreadsheet.df[['Enrl Cd', 'netID', 'Perm #', "Letter Grade Submitted", 'Email', 'ClassLevel', 'Major1', 'Major2']]
                self.master_spreadsheet.df = pd.merge(self.master_spreadsheet.df, egrades_spreadsheet.df, on=self.id_format, how ="right")
            # Webwork Spreadsheet Integration
            webwork_spreadsheet_list = [spreadsheet for spreadsheet in self.spreadsheets if spreadsheet.source == "Webwork"]
            if webwork_spreadsheet_list != []:
                webwork_spreadsheet = webwork_spreadsheet_list[0]
                #### Note that this may not work yet because we haven't found the column name associated with self.id_format (or even set it!) for the webwork spreadsheet class
                self.master_spreadsheet.df = pd.merge(self.master_spreadsheet.df, webwork_spreadsheet.df, on=self.id_format, how ="left")
                self.master_spreadsheet.max_points_hash = self.master_spreadsheet.max_points_hash | webwork_spreadsheet.max_points_hash
        
        # Curving individual columns before any totals are computed
        curve_setters_for_grade_items = [curve_setter for curve_setter in self.curve_setter_list if isinstance(curve_setter.grade_item_or_category, str)]
        for curve_setter in curve_setters_for_grade_items:
            curve_setter.set_curve()
        
        # Adding all of the columns that match each grade category
        """
        For each grading category, say, homework.name = 'Homework', then a dictionary key will be added:
        homework.spreadsheet_to_grade_items_hash["Master"] = [*All columns in the master spreadsheet with that category name*]
        """
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

            if hasattr(self, "egrades_spreadsheet"):
                if "math" in str(row.fillna("")["Major1"]).lower():
                        self.math_majors.append(student)
                elif "math" in str(row.fillna("")["Major2"]).lower():
                        self.math_majors.append(student)
            # Initializing this course for the student's grade_breakdown dictionary so that 
            # grade_category: grade_breakdown pairs can be added with each grade category as the totals are computed later
            student.grade_breakdown[self] = {}
            return student
        
        self.math_majors = []
        self.master_spreadsheet.df["Student"] = self.master_spreadsheet.df.apply(get_student_info_from_row, axis=1)
        self.roster.sort(key = lambda student: student.first_name)
        
        ### Step 3: Setting the Grade Category Columns, Computing their totals, and computing grades/assigning letter grades. THIS SHOULD BE BROKEN UP IN THE FUTURE SO CURVING CAN HAPPEN!
        """Computing Category Totals spreadsheet_to_grade_items_hash is done as follows:
        The object is the grade category, and the spreadsheet source (in this case "Master") is stored as the key for the dictionary stored in the attribute 
        spreadsheet_to_grade_items_hash. The definition is used below. 
        grade_category.spreadsheet_to_grade_items_hash[self.master_spreadsheet.source] = [column for column in self.master_spreadsheet.df.columns if grade_category.name in column]"""
        for grade_category in self.grade_categories:
            if grade_category.assignment_weighting == "equal":
                for grade_cat_col_name in grade_category.spreadsheet_to_grade_items_hash[self.master_spreadsheet.source]:
                    self.master_spreadsheet.df[grade_cat_col_name] *= 100/self.master_spreadsheet.max_points_hash[grade_cat_col_name]
                    self.master_spreadsheet.max_points_hash[grade_cat_col_name] = 100

            # Computing the Category Total
            grade_items = grade_category.spreadsheet_to_grade_items_hash[self.master_spreadsheet.source]
            
            # Quick Adjustment to make sure there aren't as many dropped assignments (or more) than there are actual assignments in a grade category. 
            # For example, if you plan on dropping the lowest 4 quizzes but there are only 3 quizzes on the gradebooks then this would make you drop the lowest 2 instead (for now). 
            drop_num = grade_category.number_of_dropped_assignments
            drop_num = min(drop_num, len(grade_items) - 1)
            
            # This control flow ensures empty categories have a zero total. When grade columns are created, these will not be factored into grade calculations. 
            if len(grade_items) > 0:
                self.master_spreadsheet.df[f"{grade_category.name} Total"] = self.master_spreadsheet.df[grade_items].apply(lambda row: sum(sorted(row.fillna(0))[drop_num:]), axis=1)
                self.master_spreadsheet.max_points_hash[f"{grade_category.name} Total"] = sum(sorted([self.master_spreadsheet.max_points_hash[item] for item in grade_items])[drop_num:])
                
                # Normalizing the Totals
                self.master_spreadsheet.df[f"{grade_category.name} Total"] *= 100/self.master_spreadsheet.max_points_hash[f"{grade_category.name} Total"]
                self.master_spreadsheet.max_points_hash[f"{grade_category} Total"] = 100
                #Rounding to Two Decimal Places
                self.master_spreadsheet.df[f"{grade_category.name} Total"] = self.master_spreadsheet.df[f"{grade_category.name} Total"].apply(np.round, decimals=2)
            else:
                self.master_spreadsheet.df[f"{grade_category.name} Total"] = 0
            
            
        # Curving individual columns before any totals are computed
        curve_setters_for_grade_items = [curve_setter for curve_setter in self.curve_setter_list if isinstance(curve_setter.grade_item_or_category, GradeCategory)]
        for curve_setter in curve_setters_for_grade_items:
            curve_setter.set_curve()
        
        # Computing grades and assigning letter grades
        self.create_grade_columns()
    
        # Mapping the category total to a student attribute
        for index, row in self.master_spreadsheet.df.iterrows():
            student = row["Student"]
            student.grades[self] = (row.fillna(0)["Grade"], row["Letter Grade"])
            for grade_category in self.grade_categories:
                student.grade_breakdown[self][grade_category] = row.fillna(0)[f"{grade_category.name} Total"]
 

    def create_pie_chart(self, renaming_dictionary = {}, style = None):
        """A figure of the pie chart will be saved in the Images folder. """
        # Making sure there's an images folder
        if not os.path.exists("Images"):
            os.mkdir("Images")
        
        # Completing the naming dictionary from the renaming dictionary
        naming_dictionary = {category.name:category.name for category in self.grade_categories} | renaming_dictionary
        
        # Setting up the style argument
        style_list = ["seaborn-paper", "fivethirtyeight"] + mpl.style.available
        if style == None:
            style = "seaborn-paper"
        elif isinstance(style, int):
            style = style_list[style%len(style_list)]

        sns.set()
        # sns.set_palette("deep")
        
        #Pie Chart
        grade_items_list = [naming_dictionary[category.name] for category in self.grade_categories]
        grade_item_percentages = [category.percent_weight for category in self.grade_categories]
        #plt.pie(grade_item_percentages, labels = grade_items_list, autopct='%0.1f%%')
        explode = [.05,.05,.05,.05, .05] # To slice the perticuler section
        colors = ["blue", "darkorange", "forestgreen", "purple",'g', "b"][:len(self.grade_categories)] # Color of each section
        textprops = {"fontsize":30} # Font size of text in pie chart

        fig1, ax1 = plt.subplots()
        with plt.style.context(style):
            a,b,m = ax1.pie(grade_item_percentages, 
                            labels = grade_items_list, 
                            radius = 2, 
                            explode=None, 
                            colors=colors, 
                            autopct='%.0f%%', 
                            textprops=textprops)
            [m[i].set_color('white') for i in range(len(m))]

        plt.savefig(f"Images/{self.quarter} {self.name} Grade Category Pie Chart.png", bbox_inches = "tight")
        plt.show(block=False)
        time.sleep(5)
        plt.close()

    def print_student_grade_breakdown(self, student_name, position = None, use_last_name = False):
        if use_last_name == True:
            first_or_last_name = "Last Name"
        else:
            first_or_last_name = "First Name"
        display_list = ["First Name", "Last Name", "Grade"]+[grade_category.name+" Total" for grade_category in self.grade_categories]+["Letter Grade"]
        print_dataframe = self.master_spreadsheet.df[self.master_spreadsheet.df[first_or_last_name].apply(lambda entry: student_name.lower() in entry.lower())][display_list]
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
    

    def plot_grade_item(self, 
                    grade_item, 
                    style = None,
                    df=None, 
                    max_score = 100, 
                    auto_max_score = True, 
                    stat = "count", 
                    save_figure = False, 
                    graph_color="mediumpurple", 
                    over_achiever_color = "rebeccapurple",
                    mean_line_color="darkred", 
                    mean_line_width = 1.5,
                    mean_line_alpha=.95, 
                    median_line_color="mediumblue", 
                    median_line_width = 2,
                    median_line_alpha=.95, 
                    show_plot = True
                   ):
        """Plots a single grade item from one of the class's dataframes. """

        def stat_label(list, median_line_color, mean_line_color):
            #used for plotting functions -- the stats are printed on the bottom
            return f"Size: {list[0]}, Mean ({mean_line_color}): {list[2]}, Median ({median_line_color}): {list[1]}, Std: {list[3]}, Min: {list[4]}, Max: {list[5]}"
                    
        style_list = ["seaborn-paper", "fivethirtyeight"] + mpl.style.available
        
        if style == None:
            style = "seaborn-paper"
        elif isinstance(style, int):
            style = style_list[style%len(style_list)]

        if df == None:
            df=self.master_spreadsheet.df
        
        sns.set()
        sns.set_palette("deep")
        
        with plt.style.context(style):
            mpl.rcParams['text.color'] = graph_color
            plt.figure(figsize = (17,6))
            plt.rcParams["axes.titlesize"] = 30 
            col = df[df[grade_item].notna()][grade_item]
            stat_list = [col.count(), np.round(col.median(), decimals=1), np.round(col.mean(), decimals=1), np.round(col.std(), decimals=1), np.round(col.min(), decimals=1), np.round(col.max(), decimals=1)]
            
            #Grade Item Max Score -- Derived from the Max Points Function
            if auto_max_score == True:
                max_score = self.master_spreadsheet.max_points_hash[grade_item]

            sns.histplot(col, 
                        kde=True, 
                        bins=[max_score/10*n for n in range(11)], 
                        stat=stat, 
                        #ax=axes[0], 
                        color=graph_color).set(title = f"{grade_item.capitalize()}", 
                                                xlabel = stat_label(stat_list, median_line_color = median_line_color, mean_line_color = mean_line_color)
                                                )
            if stat_list[-1] > max_score:
                sns.histplot(df[max_score < df[grade_item]][grade_item], 
                            bins=[max_score, stat_list[-1]], 
                            color=over_achiever_color
                            )
            
            #Dashed lines for means%
            plt.axvline(df[grade_item].mean(), linestyle = "dashdot", linewidth = mean_line_width, color = mean_line_color, alpha = mean_line_alpha)


            #Dotted Lines for Medians
            plt.axvline(df[grade_item].median(), linestyle = "dashed", linewidth = median_line_width, color = median_line_color, alpha = median_line_alpha)




        if save_figure == True:
            plt.savefig(f"Images/{self.quarter} {self.name} {grade_item} Distribution.png", bbox_inches = "tight")
        
        if show_plot == True:
            plt.show()
            time.sleep(5)
            plt.close("all")
    
        







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
        return f"{self.name} Category for {self.course}"
    
    def describe(self):
        return f"{self.name} is a grade category for {self.course}. \n" + \
                f"It's worth {self.percent_weight}% of the course grade and the lowest {self.number_of_dropped_assignments} grade items will be dropped. \n" + \
                f"Its assignments have a(n) {self.assignment_weighting} weighting when the total is calculated."

    def plot(self):
        self.course.plot_grade_item(f"{self.name} Total")

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
        if not isinstance(self.df, pd.DataFrame):
            print(f"Gradescope Spreadsheet {self} instantiated with no dataframe.")
            return None

        if isinstance(self.course, Course):
            self.course.gradescope_spreadsheet = self
        
        self.set_max_points_info()
        
        # Adding a netID column in the case where Perm # is the id_format of the course. 
        if self.course.id_format == "Perm #":
            self.df["netID"] = self.df["Email"].apply(lambda email: email.split("@")[0])
        
        self.drop_junk_columns()
        
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

        if isinstance(self.course, Course):
            self.course.egrades_spreadsheet = self       

class WebworkSpreadsheet(Spreadsheet):
    def __init__(self, course = None, file_name = None, df = None, id_format = None, id_column_name = None):
        super().__init__(course, file_name, df, id_format, id_column_name)
        self.source = "Webwork"
        """
        Still left to do: 
        1) [done for netID] Identify the id column (based on its course's id_format) and, in the case of netID, create a new SID column with the first several letters of their emails addresses
        2) Figure out format, stripping/cleaning the spaces out of the columns and column names, identifying the homework total column
        3) If we want to take a look at individual assignments, creating a max_points_hash attribute to track the maximum points for each assignment
        """
        if isinstance(self.course, Course):
            self.course.webwork_spreadsheet = self

        self.max_points_hash = {"Homework": 100}
        # If the line below throws an error, it's because the column names aren't matching
        webwork_total_col_name = [col_name for col_name in self.df.columns if r"%score" in col_name][0]

        # Student ID olumn Name entered as an argument at instantiation
        if id_column_name != None: 
            self.df[self.course.id_format] = self.df[id_column_name]
        # netID
        elif self.course.id_format == "netID": 
            id_column_name = [col_name for col_name in self.df.columns if "login ID" in col_name][0]
            self.df[self.course.id_format] = self.df[id_column_name].apply(lambda entry: entry.split("@")[0])
        # Perm #
        elif self.course.id_format == "Perm #":
            id_column_name = [col_name for col_name in self.df.columns if "ID number" in col_name][0]
            self.df[self.course.id_format] = self.df[id_column_name]
        # If we're here, then the program doesn't know where to look to identify students. So spreadsheet merging can't happen later. 
        else:
            raise Exception("The Webwork class cannot find the student id column because")
        
        self.df.rename(columns = {webwork_total_col_name: "Homework"}, inplace = True)
        self.df = self.df[[self.course.id_format, "Homework"]]
                    

        # Adding all of the columns that match each grade category
        for grade_category in self.course.grade_categories:
            grade_category.spreadsheet_to_grade_items_hash[self.source] = [column for column in self.df.columns if grade_category.name in column]

class MasterSpreadsheet(Spreadsheet):
    def __init__(self, course = None, file_name = None, df = None, id_format = None, id_column_name = "SID"):
        super().__init__(course, file_name, df, id_format, id_column_name)
        self.source = "Master"

        if isinstance(self.course, Course):
            self.course.master_spreadsheet = self
        
        



class GradeCalculator:
    def __init__(self, course):
        self.course = course
    
    def compute_standard_grades(self, master_spreadsheet = None):
        if master_spreadsheet == None:
            master_spreadsheet = self.course.master_spreadsheet


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
        """
        If the student is instantiated with a course, then 
        1) That course is added to the student's course history and
        2) The student is added to that courses's roster of students.
        """
        self.grades = {}
        if isinstance(course, Course):
            self.courses = [course]
            self.courses[0].roster.append(self)
        Student.lookup_by_netID[self.netID] = self
        Student.lookup_by_perm[self.perm_number] = self
        """
        This is a grede breakdown for each course in the student's course history. 
        The keys are the courses the student has had, i.e. self.courses. 
        The values are dictionaries for each course. 
        For those dictionaries (for each course the student has taken), 
        the keys are the Grade Categories for the course, i.e. course.grade_categories, 
        and the values are the student's percent breakdown for each category. 

        To summarize in code, 
        1) self.grade_breakdown.keys() = self.courses
        2) self.grade_breakdown.values() = [{category: percent_grade for category in course.grade_categories} for course in self.courses]
        3) For each dictionary in self.grade_breakdown.values(), 
            a) dictionary.keys() = course.grade_categories
            b) dictionary.values() = [percent_grade for category in course.grade_categories].
        """
        self.grade_breakdown = {}
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.netID}"
    
    def show_grade(self, course = None):
        if course == None:
            course = self.courses[-1]
        return self.grades[course]
    
    def create_pie_chart(self, course = None, renaming_dictionary = {}, style = None):
        """A figure of the pie chart will be saved in the Images folder. """
                
        # Setting the Course Default to the last course the student attended
        if course == None:
            course = self.courses[-1]
        # Setting up the style argument - default to seaborn-paper, and numbers can also be entered
        style_list = ["seaborn-paper", "fivethirtyeight"] + mpl.style.available
        if style == None:
            style = "seaborn-paper"
        elif isinstance(style, int):
            style = style_list[style%len(style_list)]

        # Making sure there's an images folder
        if not os.path.exists("Images"):
            os.mkdir("Images")
        
        if not os.path.exists("Images/Student Grade Breakdown Pie Charts"):
            os.mkdir("Images/Student Grade Breakdown Pie Charts")

        # Completing the naming dictionary from the renaming dictionary
        naming_dictionary = {category.name:category.name for category in course.grade_categories} | renaming_dictionary
        
        sns.set()
        # sns.set_palette("deep")
        
        # Pie Chart
        # Generating the list of grade item percentages using the grading categories associated with the given course
        grade_category_list = [naming_dictionary[category.name] for category in course.grade_categories]
        grade_category_percent_weights = [category.percent_weight for category in course.grade_categories]

        # Zipping in the empty labels and complementary percentages
        # pie_chart_labels = [label for label in [naming_dictionary[cat.name], ""] for cat in course.grade_categories]
        # pie_chart_percentages = [percentage for percentage in [self.grade_breakdown[course][category]*.01*category.percent_weight, (100-self.grade_breakdown[course][category]*.01*category.percent_weight)] for category in course.grade_categories]
        from itertools import chain
        # Pie Chart Labels: the commented-out line below expresses the category as a percent grade out of the category weight. I think this probably hard for students to read. 
        # pie_chart_labels = list(chain.from_iterable([[f"{naming_dictionary[category.name]}: {np.rint(self.grade_breakdown[course][category])}% of {category.percent_weight}", ""] for category in course.grade_categories]))
        pie_chart_labels = list(chain.from_iterable([[f"Your {naming_dictionary[category.name]}", ""] for category in course.grade_categories]))
        pie_chart_percentages = list(chain.from_iterable([[self.grade_breakdown[course][category]*.01*category.percent_weight, ((100-self.grade_breakdown[course][category])*.01*category.percent_weight)] for category in course.grade_categories]))
        display_percentages = list(chain.from_iterable([[f"{self.grade_breakdown[course][category]}% of {category.percent_weight}%", ""] for category in course.grade_categories]))


        #plt.pie(grade_item_percentages, labels = grade_items_list, autopct='%0.1f%%')
        explode = [.05,.05,.05,.05, .05] # To slice the perticuler section
        grade_percentage_colors = ["blue", "darkorange", "forestgreen", "purple",'g', "b"][:len(course.grade_categories)] # Color of each section
        # The colors list is created by staggering white slices with the grade percentage colors. 
        colors = list(chain.from_iterable([[grade_percentage_color, darken_color(grade_percentage_color, .7)] for grade_percentage_color in grade_percentage_colors]))
        textprops = {"fontsize":30} # Font size of text in pie chart

        fig1, ax1 = plt.subplots()
        with plt.style.context(style):
            a,b,m = ax1.pie(pie_chart_percentages, 
                            labels = pie_chart_labels, 
                            radius = 2, 
                            explode=None, 
                            colors=colors, 
                            autopct='%.0f%%', 
                            wedgeprops = {"edgecolor" : "white",
                                          'linewidth': 2,
                                          'antialiased': True},
                            textprops=textprops)
            [m[i].set_color('white') for i in range(len(m)) if i%2 == 0]
            [m[i].set_color('darkgrey') for i in range(len(m)) if i%2 == 1]
            [m[i].set_text("") for i in range(len(m))]# if i%2 == 1]
            
        plt.savefig(f"Images/Student Grade Breakdown Pie Charts/{self.first_name} {self.last_name} {course.quarter} {course.name} Grade Breakdown Pie Chart.png", bbox_inches = "tight")
        # plt.close()

    
    def create_other_pie_chart(self, course = None, renaming_dictionary = {}, style = None):
        """A figure of the pie chart will be saved in the Images folder. """
                
        # Setting the Course Default to the last course the student attended
        if course == None:
            course = self.courses[-1]
        # Setting up the style argument - default to seaborn-paper, and numbers can also be entered
        style_list = ["seaborn-paper", "fivethirtyeight"] + mpl.style.available
        if style == None:
            style = "seaborn-paper"
        elif isinstance(style, int):
            style = style_list[style%len(style_list)]

        # Making sure there's an images folder
        if not os.path.exists("Images"):
            os.mkdir("Images")
        
        if not os.path.exists("Images/Student Grade Breakdown Pie Charts"):
            os.mkdir("Images/Student Grade Breakdown Pie Charts")

        # Completing the naming dictionary from the renaming dictionary
        naming_dictionary = {category.name:category.name for category in course.grade_categories} | renaming_dictionary
        
        sns.set()
        # sns.set_palette("deep")
        
        # Pie Chart
        # Generating the list of grade item percentages using the grading categories associated with the given course
        grade_category_list = [naming_dictionary[category.name] for category in course.grade_categories]
        grade_category_percent_weights = [category.percent_weight for category in course.grade_categories]

        # Zipping in the empty labels and complementary percentages
        # pie_chart_labels = [label for label in [naming_dictionary[cat.name], ""] for cat in course.grade_categories]
        # pie_chart_percentages = [percentage for percentage in [self.grade_breakdown[course][category]*.01*category.percent_weight, (100-self.grade_breakdown[course][category]*.01*category.percent_weight)] for category in course.grade_categories]
        from itertools import chain
        # Pie Chart Labels: the commented-out line below expresses the category as a percent grade out of the category weight. I think this probably hard for students to read. 
        # pie_chart_labels = list(chain.from_iterable([[f"{naming_dictionary[category.name]}: {np.rint(self.grade_breakdown[course][category])}% of {category.percent_weight}", ""] for category in course.grade_categories]))
        pie_chart_labels = [f"{naming_dictionary[category.name]}" for category in course.grade_categories] + ["" for category in course.grade_categories]
        pie_chart_percentages = [self.grade_breakdown[course][category]*.01*category.percent_weight for category in course.grade_categories] + [((100-self.grade_breakdown[course][category])*.01*category.percent_weight) for category in course.grade_categories]
        display_percentages = list(chain.from_iterable([[f"{self.grade_breakdown[course][category]}% of {category.percent_weight}%", ""] for category in course.grade_categories]))


        #plt.pie(grade_item_percentages, labels = grade_items_list, autopct='%0.1f%%')
        explode = [.05,.05,.05,.05, .05] # To slice the perticuler section
        grade_percentage_colors = ["blue", "darkorange", "forestgreen", "purple",'g', "b"][:len(course.grade_categories)] # Color of each section
        # The colors list is created by staggering white slices with the grade percentage colors. 
        colors = [grade_percentage_color for grade_percentage_color in grade_percentage_colors] + [darken_color(grade_percentage_color, .7) for grade_percentage_color in grade_percentage_colors]
        textprops = {"fontsize":30} # Font size of text in pie chart

        fig1, ax1 = plt.subplots()
        with plt.style.context(style):
            for k in range(3):
                a,b,m = ax1.pie(pie_chart_percentages, 
                                labels = pie_chart_labels, 
                                radius = 2, 
                                explode=None, 
                                colors=colors, 
                                autopct='%.0f%%', 
                                wedgeprops = {"edgecolor" : "white",
                                            'linewidth': k,
                                            'antialiased': True},
                                textprops=textprops)
                [m[i].set_color('white') for i in range(len(m))]
                [m[i].set_text("") for i in range(len(m)) if i > k]
                plt.pause(1)
            
        # plt.savefig(f"Images/Student Grade Breakdown Pie Charts/{self.first_name} {self.last_name} {course.quarter} {course.name} Grade Breakdown Pie Chart.png", bbox_inches = "tight")
        plt.show()
        # plt.close()


    def create_incremented_pie_chart(self, increment, course = None, renaming_dictionary = {}, style = None):
        """A figure of the pie chart will be saved in the Images folder. """
                
        # Setting the Course Default to the last course the student attended
        if course == None:
            course = self.courses[-1]
        # Setting up the style argument - default to seaborn-paper, and numbers can also be entered
        style_list = ["seaborn-paper", "fivethirtyeight"] + mpl.style.available
        if style == None:
            style = "seaborn-paper"
        elif isinstance(style, int):
            style = style_list[style%len(style_list)]

        # Making sure there's an images folder
        # Completing the naming dictionary from the renaming dictionary
        naming_dictionary = {category.name:category.name for category in course.grade_categories} | renaming_dictionary
        
        sns.set()
        # sns.set_palette("deep")
        
        # Pie Chart
        # Generating the list of grade item percentages using the grading categories associated with the given course
        grade_category_list = [naming_dictionary[category.name] for category in course.grade_categories]
        grade_category_percent_weights = [category.percent_weight for category in course.grade_categories]
        num_categories = len(course.grade_categories)

        plt.style.use('seaborn-pastel')

        fig, ax = plt.subplots()
        
        def function_to_draw_figure(increment):
            # Zipping in the empty labels and complementary percentages
            # pie_chart_labels = [label for label in [naming_dictionary[cat.name], ""] for cat in course.grade_categories]
            # pie_chart_percentages = [percentage for percentage in [self.grade_breakdown[course][category]*.01*category.percent_weight, (100-self.grade_breakdown[course][category]*.01*category.percent_weight)] for category in course.grade_categories]
            from itertools import chain
            # Pie Chart Labels: the commented-out line below expresses the category as a percent grade out of the category weight. I think this probably hard for students to read. 
            # pie_chart_labels = list(chain.from_iterable([[f"{naming_dictionary[category.name]}: {np.rint(self.grade_breakdown[course][category])}% of {category.percent_weight}", ""] for category in course.grade_categories]))
            pie_chart_labels = list(chain.from_iterable([[f"Your {naming_dictionary[category.name]}", ""] for category in course.grade_categories]))+["" for category in course.grade_categories]
            pie_chart_percentages = list(chain.from_iterable([[self.grade_breakdown[course][category]*.01*category.percent_weight, ((1-increment)*(100-self.grade_breakdown[course][category])*.01*category.percent_weight)] for category in course.grade_categories]))+[(increment*(100-self.grade_breakdown[course][category])*.01*category.percent_weight) for category in course.grade_categories]
            display_percentages = list(chain.from_iterable([[f"{self.grade_breakdown[course][category]}% of {category.percent_weight}%", ""] for category in course.grade_categories])) + [""]*num_categories


            #plt.pie(grade_item_percentages, labels = grade_items_list, autopct='%0.1f%%')
            explode = [.05]*num_categories # To slice the perticuler section
            grade_percentage_colors = ["blue", "darkorange", "forestgreen", "purple",'g', "b"][:len(course.grade_categories)] # Color of each section
            # The colors list is created by staggering white slices with the grade percentage colors. 
            colors = list(chain.from_iterable([[grade_percentage_color, darken_color(grade_percentage_color, .7)] for grade_percentage_color in grade_percentage_colors]))+[darken_color(grade_percentage_color, .7) for grade_percentage_color in grade_percentage_colors]
            textprops = {"fontsize":30} # Font size of text in pie chart

            fig, ax = plt.subplots()
            with plt.style.context(style):
                a,b,m = ax.pie(pie_chart_percentages, 
                                labels = pie_chart_labels, 
                                radius = 2, 
                                explode=None, 
                                colors=colors, 
                                autopct='%.0f%%', 
                                wedgeprops = {"edgecolor" : "white",
                                            'linewidth': 2,
                                            'antialiased': True},
                                textprops=textprops)
                [m[i].set_color('white') for i in range(len(m)) if i%2 == 0]
                [m[i].set_color('darkgrey') for i in range(len(m)) if i%2 == 1]
                [m[i].set_text("") for i in range(len(m))]# if i%2 == 1]
                
            # plt.savefig(f"Images/Student Grade Breakdown Pie Charts/{self.first_name} {self.last_name} {course.quarter} {course.name} Grade Breakdown Pie Chart.png", bbox_inches = "tight")
            # plt.show(block=False)
        ani = FuncAnimation(fig, function_to_draw_figure, frames=range(int(1/increment)), repeat=True)

        return ani

        
    
    




    
        


class CurveSetter:
    def __init__(self, 
                 value, 
                 grade_item_or_category, 
                 course = None, 
                 method = "Percent of Missing Points", 
                 spreadsheet = None, 
                 point_ceiling = False, 
                 custom_row_function = None
                 ):
        self.grade_item_or_category = grade_item_or_category
        # Numerical value used in curving
        self.value = value
        # Setting the course value by the grade_item_category in the case that it's a GradeCategory
        if course == None:
            if isinstance(grade_item_or_category, GradeCategory):
                course == self.grade_item_or_category.course
            else: 
                raise Exception("A value for course must be entered if the grade_item_or_category argument is not a GradeCategory.")
        self.course = course
        # Boolean answering whether or not values above 100% are allowed. 
        self.point_ceiling = point_ceiling
        # How the curve will be set (see valid method arguments below)
        self.method = method
        """
        CurveSetter method arguments are:
            "Percent of Missing Points" - returns a percentage (self.value %) of missing points from a perfect score
            "New Ceiling" - Sets the Ceiling to something different
            "Lower Ceiling to Highest Score" - is a specific example of "New Ceiling" that lowers the ceiling to the maximum score.
            "Add Points" - adds points to everyone's point total
            "Move Everyone Up" - is a specific example of "Add Points" that adds points to everyone so the maximum score is 100%
            "Custom" - applies a custom function to the df in order to modify the column in question. 
            Caution: If you use "Custom", you need your custom_row_function parameter to take a ROW argument, but the output needs to be the entry for the curved grade column. 
        """
        self.spreadsheet = spreadsheet
        self.custom_row_function = custom_row_function

        # Determining the dataframe and column to be curved
        # dataframe
        if spreadsheet == None:
            spreadsheet = self.course.master_spreadsheet
        # Adds this object to the list of grade setters for self.course.
        self.course.curve_setter_list.append(self)

    def set_curve(self):
        # Column to be curved    
        if self.spreadsheet == None:
            self.spreadsheet = self.course.master_spreadsheet
        if isinstance(self.grade_item_or_category, GradeCategory):
            if self.grade_item_or_category.course == self.course:
                curve_column = self.spreadsheet.df[self.grade_item_or_category.name + " Total"]
                max_score = 100
            else:
                raise Exception("The course for the argument grade_item_or_category does not match the course given.")
        elif isinstance(self.grade_item_or_category, str):
            if self.grade_item_or_category in self.spreadsheet.df.columns:
                curve_column = self.spreadsheet.df[self.grade_item_or_category]
                max_score = self.spreadsheet.max_points_hash[self.grade_item_or_category]
        
            else:
                raise Exception(f"The argument grade_item_or_category is not in {self.spreadsheet.df}.columns")
        else:
            raise Exception(f"The argument grade_item_or_category must be either a category of the course or a string.")
        
        # Curving
        if self.method == "Percent of Missing Points":
            self.spreadsheet.df[curve_column.name] = curve_column.apply(lambda entry: entry + self.value*.01*(max_score - entry)).apply(np.round, decimals = 2)
            print(max_score)
        elif self.method == "New Ceiling":
            if isinstance(self.grade_item_or_category, str):
                self.spreadsheet.max_points_hash[curve_column.name] = self.value # Just resets the max points score
            elif isinstance(self.grade_item_or_category, GradeCategory):
                self.spreadsheet.df[curve_column.name] = curve_column.apply(lambda entry: entry*100/self.value).apply(np.round, decimals = 2) # Makes the percentage out of value% instead of 100%
        elif self.method == "Lower Ceiling to Highest Score":
            self.spreadsheet.df[curve_column.name] = curve_column.apply(lambda entry: entry + self.value*.01*(max_score - entry)).apply(np.round, decimals = 2)
        elif self.method == "Add Points":
            self.spreadsheet.df[curve_column.name] += self.value
        elif self.method == "Move Everyone Up":
            self.spreadsheet.df[curve_column.name] += max_score - curve_column.max()
        elif self.method == "Custom":
            self.spreadsheet.df[curve_column.name] = self.spreadsheet.df.apply(self.custom_row_function, axis=1).apply(np.round, decimals=2)
        else:
            raise Exception(f"A curve method entered was {self.method}. It must be one of the valid methods for this class")
        

        # Applying the ceiling if there needs to be one. 
        if self.point_ceiling == True:
            self.spreadsheet.df[curve_column.name] = curve_column.apply(lambda entry: min([entry, max_score]))







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


def darken_color(color, amount=1.5):
    """
    Lightens the given color by multiplying (1-luminosity) by the given amount.
    Input can be matplotlib color string, hex string, or RGB tuple.

    Examples:
    >> darken_color('g', 0.3)
    >> darken_color('#F034A3', 0.6)
    >> darken_color((.3,.55,.1), 0.5)
    """
    import matplotlib.colors as mc
    import colorsys
    try:
        c = mc.cnames[color]
    except:
        c = color
    c = colorsys.rgb_to_hls(*mc.to_rgb(c))
    return colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])
