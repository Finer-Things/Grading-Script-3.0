This project is all about the Course Class module, which provides an object-oriented framework to automate just about everything I need to do with student data in a variety of ways, differing with each course I teach. 
# Course Class
## Grading Functionality
* Tracks student data across the different record-keeping platforms, navigating two student id systems used by the campus. 
* Automates the calculation of grades based on scores, grade categories (e.g. "Quiz Total", "Homework Total", etc.) and their weights.
*   Multiple curving methods can be applied to individual assignments/exams, or to an entire grade category. See the CurveSetter class inside the file for a list of options.
*   Creates a csv file formatted for grade submission at the end of the quarter, so submitting grades is just a drag and drop process.
*   Multiple letter grade schemes can be used
*   Grade category totals can be calculated either by raw score or with assignments weighted equally. A number can be specified as the number of lowest grade items to be dropped in that category during this computation. Grade categories can have no assignments while grades are computed without a division by zero error for grade computation. A "grade so far" is calculated instead for each student.
*   Tracks student performance across multiple courses to facilitate the process of writing letters of recommendation.
*   Keyword search functionality within each course to find students and see their current breakdown, view a pie chart of ther performance by category, and calculate what score they would need on the final in order to obtain a desired grade.
Examples:
* student.show_grade_breakdown()
James Bond licensetokill007
Midterm      |Quiz         |Homework     |Final        |Grade        |Letter Grade |
93.695       |91.0         |100.0        |74.5         |88.93        |B+           |
All grade categories have assignments in them.
*student.create_pie_chart()
![Student Pie Chart](https://github.com/Finer-Things/Grading-Script-3.0/assets/96888276/6c92dfe1-d56a-4abb-b494-a12f319f3da4)

## Data Visualizations
* Performance Histogram: This colorful histogram can be easily generated for any assignment, exam, category total (quiz grade, homework grade, etc) or overall performance to-date in the class. The class-wide scores are visible as a distribution using a kernel density estimator along with the histogram so the modality of student performance can be quickly assessed. The bins are by letter grade range (A's, B's, etc) and max scores are retained behind the scenes to allow for any scores over 100% to be displayed so they can be given their own bin. This bin has a smaller width and darker color. The mean and median are visually included with dotted lines and basic stats are printed at the bottom of the image.
![Spring 2023 Math 4B Final Distribution](https://github.com/Finer-Things/Grading-Script-3.0/assets/96888276/42c80305-7bc8-46d1-b610-6280209f16c5)
* Bar Graph of Letter Grades: In addition to seeing the histogram above for class performance, this organizes all of the letter grades into one colorful bar graph so the user can quickly see the frequency of each letter grade, including A+'s, A-'s, etc.
![Spring 2023 Math 4B Letter Grades](https://github.com/Finer-Things/Grading-Script-3.0/assets/96888276/46cd455a-52af-4e25-8d1e-bb9df7669aa2)
* Visual Linear Regression Assumption Test: This test allows for a quick visual check of homeoscedasticity and uniformity, the two assumptions that need to be true in order for linear regression to be a good model for a feature to predict an outcome. Because of the clustering of student scores around 100% and the small sample sizes, machine learning has been best suited for finding student outliers who can be reached out to in case something happened mid quarter. This is a good example, taken from a course I taught a year ago. 
![Linear Regression Hypotheses](https://github.com/Finer-Things/Grading-Script-3.0/assets/96888276/c472bc0a-cc34-4e1a-a4bc-410ff65fa0f6)

