This project is all about the Course Class module, which provides an object-oriented framework to automate just about everything I need to do with student data in a variety of ways, differing with each course I teach. 
# Course Class
## Grading Functionality
* Tracks student data across several record-keeping platforms, simultaneously handling two conflicting student id systems used by my own campus. 
* Automates the calculation of grades with a customizable framework based on scores, grade categories (e.g. "Quiz Total", "Homework Total", etc.) and their weights.
  * Multiple curving methods can be applied to individual assignments/exams, or to an entire grade category. See the CurveSetter class inside the file for a list of options.
  * Creates a csv file formatted for grade submission at the end of the quarter, so submitting grades is simply a drag and drop process.
  * Flexible letter grade assignment to accomodate Math 34's "Great Effort Rule."
  * Grade category totals can be calculated either by raw score or with assignments weighted equally. A number can be specified as the number of lowest grade items to be dropped in that category during this computation. Grade categories can have no assignments while grades are computed without a division by zero error for grade computation. A "grade so far" is calculated instead for each student. As soon as grade category totals are set, you can make a pie chart to show the breakdown by category. I use these for my syllabus at the beginning of each quarter.
![Spring 2023 Math 4B Grade Category Pie Chart](https://github.com/Finer-Things/Grading-Script-3.0/assets/96888276/675ddeab-5127-427e-8d00-76a9d98c4e46)
  * Tracks student performance across multiple courses to facilitate the process of writing letters of recommendation.
  * Keyword search functionality within each course to find students and see their current breakdown, view a pie chart of ther performance by category, and calculate what score they would need on the final in order to obtain a desired grade.
Examples:
    * student.show_grade_breakdown()
![image](https://github.com/Finer-Things/Grading-Script-3.0/assets/96888276/f02b49ce-881c-4081-a643-92ad089968a6)
    * student.create_pie_chart()
![Spring 2023 Math 4B Grade Category Pie Chart](https://github.com/Finer-Things/Grading-Script-3.0/assets/96888276/1223d508-2744-4b98-92fe-45817f6b3b41)

## Data Visualizations
* Performance Histogram: This histogram can be easily generated for any assignment, exam, category total (quiz grade, homework grade, etc) or overall performance to-date in the class. The class-wide scores are visible as a distribution using a kernel density estimator along with the histogram so the modality of student performance can be quickly assessed. The bins are by letter grade range (A's, B's, etc) and max scores are retained behind the scenes to allow for any scores over 100% to be displayed so they can be given their own bin. This bin has a smaller width and darker color. The mean and median are visually included with dotted lines and basic stats are printed at the bottom of the image.
![Spring 2023 Math 4B Final Distribution](https://github.com/Finer-Things/Grading-Script-3.0/assets/96888276/42c80305-7bc8-46d1-b610-6280209f16c5)
* Bar Graph of Letter Grades: In addition to seeing the histogram above for class performance, this organizes all of the letter grades into one colorful bar graph so the user can quickly see the frequency of each letter grade, including A+'s, A-'s, etc.
![Spring 2023 Math 4B Letter Grades](https://github.com/Finer-Things/Grading-Script-3.0/assets/96888276/465bac70-8152-499f-af1a-cf4ed2d1073e)
* Testing Visual Linear Regression Assumptions: This test allows for a quick visual check of homeoscedasticity and uniformity, the two assumptions that need to be true in order for linear regression to be a good model for a feature to predict an outcome. Because of the clustering of student scores around 100% and the small sample sizes. who can be reached out to in case something happened mid quarter. Below is an example, taken from a course I taught a year ago. 
![Linear Regression Hypotheses](https://github.com/Finer-Things/Grading-Script-3.0/assets/96888276/c472bc0a-cc34-4e1a-a4bc-410ff65fa0f6)

