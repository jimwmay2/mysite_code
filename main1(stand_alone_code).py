import csv
import pandas as pd
from pandas import ExcelWriter
from pandas import ExcelFile
import numpy as np
from scipy import stats
from decimal import*
from sklearn import datasets, linear_model
import seaborn as sns
import re
import time
from datetime import*
from collections import*
from itertools import filterfalse
from plotly.offline import init_notebook_mode, iplot
from IPython.display import display, HTML
import plotly.offline as offline
import plotly.graph_objs as go
import pickle
"""to install modules, type in 'pip3 install' followed by the module name.  Enter this in the operating system command line"""
"""Ensure folder 'Graphs'is created in directory with all raw files"""

class student(object):              #defining student class
    """docstring for student."""
    def __init__(self, name):
        self.name = name
        self.exams = []
        self.hw =    []
        self.grade = 0
        self.rolling_grade = []
        self.clicks = []            #when filled, will be a list of lists
        self.weeks = {}             #fillled when in course
        self.activity = {}

    def add_exam(self, arg):
        self.exams.append(arg)

    def add_hw(self, arg):
        self.hw.append(arg)

    def calc_rolling_grade(self, arg):
        exam_average = 0
        if arg is "average":
            for week in range(1,12):
                if week <= 4:
                    exam_average = self.exams[0]
                elif week >= 5 and week < 8:
                    exam_average = (self.exams[0] + self.exams[1])/2
                elif week >= 8:
                    exam_average = (self.exams[0] + self.exams[1] + self.exams[2])/3
                self.rolling_grade.append(exam_average)
        else:
            for week in range(1,12):
                if week <= 4:
                    exam = self.exams[0]
                elif week >= 5 and week < 8:
                    exam = self.exams[1]
                elif week >= 8:
                    exam = self.exams[2]
                self.rolling_grade.append(exam)
        #print(self.name, self.rolling_grade)

    def add_activity(self, activity, search_arg):
        temp = []
        for c in self.clicks:
            if not isinstance(c[0][0], float):
                if search_arg in c[0][0].lower() or search_arg in c[0][1].lower():
                    temp.append(c)
        self.activity[activity] = temp

    def remove_activity(self, activity):
        if activity in self.activity:
            del self.activity[activity]

    def add_clicks(self, arg, arg1):
        d = datetime.strptime(arg1, "%m/%d/%Y - %H:%M")     #store as a date data type
        list1 = [arg, d]
        if len(self.clicks) > 0:
            if list1[0] is not self.clicks[len(self.clicks)-1][0]:          #makes sure the page title isnt the same
                self.clicks.append(list1)
            elif list1[1].hour is not self.clicks[len(self.clicks)-1][1].hour or list1[1].minute is not self.clicks[len(self.clicks)-1][1].minute:        #makes sure entries arent repeats in the same minute
                self.clicks.append(list1)
        else:
            self.clicks.append(list1)

    def concat(self, plot):
        temp = []
        for p in plot:
            temp += self.activity[p]
        return temp

class course(object):
    """docstring for course."""
    def __init__(self, name, start_date, end_date):
        day = timedelta(days = 1)

        self.name = name
        self.start_date = datetime.strptime(start_date, '%m/%d/%Y') - (4*day)     # -5 days makes it start on a wednesday
        self.end_date = datetime.strptime(end_date, '%m/%d/%Y')
        self.students = []
        self.activities = []

    def in_course(self, arg):                           # used to filter out datapoints not in timeline
        day = timedelta(days = 1)

        if  arg[1]+day > self.end_date or arg[1] < self.start_date:
            return True
        else:
            return False

    def add_students(self, file1, file2):
        """Imports grade book-------------------------------------------------------------------------------------------------------"""
        student_list = []
        #next(file1)                                      #skip header
        #print('1')
        for row in file1.index:
            x = student(file1['Student'][row])                         # initializes a student class with student name in column 2
            for col in file1.columns:
                if file1[col][row] == ' ':              #just in case someone forgets to enter a grade
                    break
                grade_percent = file1[col][row]
                if str(file1[col][row]).isdigit():
                    grade_percent = float(file1[col][row])
                    if grade_percent > 2:                   #used 2 because sometimes there is a nerd with over 100%
                        grade_percent *= 100
                if 'hw' in col:                         #insure there are no integers in the header
                    x.add_hw(grade_percent)
                elif 'M1%' in col:
                    x.add_exam(grade_percent)
                elif 'M2%' in col:
                    x.add_exam(grade_percent)
                elif 'F%' in col:
                    x.add_exam(grade_percent)
                elif 'grade %' in col:
                    x.grade = grade_percent
            x.calc_rolling_grade('average')
            student_list.append(x)
        """Imports grade book-------------------------------------------------------------------------------------------------------"""

        """Imports online activity--------------------------------------------------------------------------------------------------"""
        i=0
        for row in file2.index:                                     #checks each row in the file
            if student_list[i].name == file2['StudentID'][row]:                  #checks if the student name is correct
                if 'welcome' or 'cas' not in file2['Path'][row]:
                    temp00 = [file2['Path'][row],file2['Page title'][row]]
                    student_list[i].add_clicks(temp00,file2['Timestamp'][row])
            else:
                if (i+1) < len(student_list):                                   #checks if it is not the end of student list
                    if student_list[i+1].name == file2['StudentID'][row]:        #checks if the next student name is correct
                        i+=1
                        if 'welcome' or 'cas' not in file2['Path'][row]:
                            temp00 = [file2['Path'][row],file2['Page title'][row]]
                            student_list[i].add_clicks(temp00,file2['Timestamp'][row])
        """Imports online activity--------------------------------------------------------------------------------------------------"""

        """Removes data not occuring in timeline------------------------------------------------------------------------------------"""
        week = timedelta(weeks = 1)                             #time steps
        day = timedelta(days = 1)                               #time steps
        #weeks = list(range(1,12))                              #list from 1-11 for course weeks
        for s in student_list:                                       #for each student
            #print(s.name)
            s.clicks[:] = filterfalse(self.in_course,s.clicks)  #removes clicks not in course timeline
            for c in s.clicks:                                  #for each video
                for r in range(1,12):                           #assigns the video a course week
                    if r == 11:
                        if (self.end_date) > c[1] >= (self.start_date + (r-1)*week):
                            c.append(r)
                    elif (self.start_date + r*week) > c[1] >= (self.start_date + (r-1)*week):
                        c.append(r)
                    for d1 in range(1,8):
                        if (self.start_date + (r-1)*week + d1*day) == c[1]:
                            c.append(d1)
            self.students.append(s)                             #adds the student       #dont change, very important
        """Removes data not occuring in timeline------------------------------------------------------------------------------------"""

    def new_activity(self, activity, search_by):
        if activity.lower() not in self.activities:
            print("new activity")
            self.activities.append(activity.lower())
            for s in self.students:
                s.add_activity(activity, search_by.lower())

    def del_activity(self, activity):
        if activity in self.activities:
            self.activities.remove(activity)
        for s in self.students:
            s.remove_activity(activity)

    def check_activity(self, datasets):
        datasets =  datasets.split()
        temp = []
        for d in datasets:
            for a in self.activities:
                if d in a:
                    temp.append(d)
        return temp

    def group_by_grade(self, weeks = None):                                     #used to display students grouped by grade.  Weeks is an optional arg
        grades = {"40's":[], "50's":[],"60's":[],"70's":[],"80's":[],"90's":[]}
        grades = OrderedDict(sorted(grades.items(), key=lambda t: t[0]))        #stores grades in order(dictionaries are normally unordered)

        if weeks is None:
            for s in self.students:             #stores students in dictionary according to final grade
                i=.5
                for key in grades:
                    if i==.5:
                        if s.grade < i and s.grade >= 0:
                            grades[key].append(s)
                    elif s.grade < i and s.grade >= (i-.1):
                        grades[key].append(s)
                    i+=.1
        else:
            for s in weeks:                     #for each week, makes a dictionary of grades
                i=.5
                for key1 in grades:
                    if i==.5:
                        if s.grade < i and s.grade >= 0:
                            grades[key].append(s)
                    elif s.grade < i and s.grade >= (i-.1):
                        grades[key1].append(s)
                    i+=.1
        return grades

    def group_by_weeks(self, grades = None, plot = None):          #grades is optional arg.
        video_weeks = {}                 #creating another dictionary is more expensive but easier to troubleshoot
        clicks_weeks = {}
        for r in range(1,12):           #creates weeks dictionary
            video_weeks[r] = []
            clicks_weeks[r] = []
        if grades is None:              #for listing students by final grade(not for graphing)
            if plot is None:
                for key1 in clicks_weeks:
                    for s1 in self.students:
                        temp = student(s1.name)
                        temp.grade = s1.grade
                        temp.rolling_grade = s1.rolling_grade
                        temp.activity = s1.activity
                        for v1 in s1.clicks:                            #student object only contains datapoints in the week it is in
                            if v1[2] == key1:                           #v[2] is the week number
                                temp.clicks.append(v1)
                        clicks_weeks[key1].append(temp)
                    clicks_weeks[key1] = self.group_by_grade(clicks_weeks[key1])    #groups each week list by grades
                return clicks_weeks
            else:
                for key in video_weeks:     #fills each week with full list of students
                    for s in self.students:
                        temp = student(s.name)
                        temp_videos = []
                        temp.grade = s.grade
                        temp.rolling_grade = s.rolling_grade
                        temp.activity = s1.activity
                        if not isinstance(plot, str):
                            activity_list = s.concat(plot)                      #plot is list of what dictionaries to access
                            for v in activity_list:                             #student object only contains datapoints in the week it is in
                                if v[2] == key:                                 #v[2] is the week number
                                    temp_videos.append(v)
                        else:
                            for v in s.activity[plot]:                          #student object only contains datapoints in the week it is in
                                if v[2] == key:                                 #v[2] is the week number
                                    temp_videos.append(v)
                        temp.activity = {"plot_list": temp_videos}
                        video_weeks[key].append(temp)
                    video_weeks[key] = self.group_by_grade(weeks[key])          #groups each week list by grades
                return video_weeks
        else:                       #for graphing student data
            if plot is None:        #for clicks
                for key1 in clicks_weeks:
                    for s1 in grades:
                        temp = student(s1.name)

                        temp_acts = {}
                        temp.grade = s1.grade
                        temp.rolling_grade = s1.rolling_grade
                        for v1 in s1.clicks:
                            #if len(v1) <= 2:
                            #    print("less than 2: ",s1.name,s1.grade,v1)
                            #if len(v1) > 3:
                            #    print("greater than 3: ",s1.name,s1.grade,v1)
                            #if len(v1) == 3:
                                #print(s1.name,key1, v1[1],v1[2])
                            if len(v1) >= 3:
                                if v1[2] == key1:                           #only appends data in the week it's in
                                    #print(s1.name,key1, v1[1],v1[2])
                                    temp.clicks.append(v1)
                        for keys, a in s1.activity.items():
                            temp_act = []
                            for i in a:
                                if len(i) >= 3:
                                    if i[2] == key1:                           #only appends data in the week it's in
                                        temp_act.append(i)
                            temp.activity[keys] = temp_act

                            #else:
                            #    print()#s1.name,key1, v1[1]
                        clicks_weeks[key1].append(temp)
                        #print(key1,len(clicks_weeks[key1]))
                return clicks_weeks
            else:
                for key in video_weeks:         #fills each week with a dictionary of grades,
                    for s in grades:            #copies and appends students data
                        temp = student(s.name)
                        temp_videos = []
                        temp.grade = s.grade
                        temp.rolling_grade = s.rolling_grade
                        for v in s.activity[plot]:      #only appends data in the week it's in
                            if v[2] == key:
                                temp_videos.append(v)
                        temp.activity = {plot: temp_videos}
                        video_weeks[key].append(temp)
                return video_weeks

    def group_by_days(self, week_number, grades):           #creating another dictionary is more expensive but easier to troubleshoot
        video_days = {}
        clicks_days = {}
        for d in range(1,8):           #creates weeks dictionary
            video_days[d] = []
            clicks_days[d] = []
            for key in video_days:
                for s in grades:
                    temp = student(s.name)
                    temp_videos = []
                    temp.grade = s.grade
                    for v in s.activity["videos"]:
                        if len(v) is 4:
                            if v[2] == week_number and v[3] == key:
                                temp_videos.append(v)
                    temp.activity = {"videos": temp_videos}
                    video_days[key].append(temp)
            for key1 in clicks_days:
                for s1 in grades:
                    temp = student(s1.name)
                    temp.grade = s1.grade
                    #print(s1.name,s1.clicks)
                    for v1 in s1.clicks:
                        #if len(v1) == 4:                            # must fix bug later
                            #print(s1.name,key1, v1[1],v1[2])
                        if v1[2] == week_number and v1[3] == key1:
                            #print(s1.name,key1, v1[1],v1[2])
                            temp.clicks.append(v1)
                        #else:
                        #    print()#s1.name,key1, v1[1]
                    clicks_days[key1].append(temp)
                    #print(key1,len(clicks_weeks[key1]))
        weeks = [video_days, clicks_days]
        return weeks

    def std_filter(self,data, deviation):
        data = np.array(data)
        mean = np.mean(data, axis=0)
        sd = np.std(data, axis=0)
        final_data = [x for x in data if (x > mean - deviation * sd)]
        final_data = [x for x in final_data if (x < mean + deviation * sd)]
        final_data = list(final_data)
        return final_data

    def plot_agg(self, plot, search_by = None):
        grades = self.group_by_grade()
        data = []
        if search_by is not None:
            self.new_activity(plot, search_by)
        for key1, students in grades.items():                              #for students in each grade
            x = []
            y = []
            for s in students:
                name_text = key1 + "<br> N=" + str(len(students)) #<br> is an html line break since plotly is html based
                if not isinstance(plot, str):
                    activity_list = s.concat(plot)
                    if len(s.activity_list) > 0:
                        y.append(len(s.activity_list))
                        x.append(name_text)
                elif search_by is None:
                    if len(s.clicks) > 0:
                        y.append(len(s.clicks))
                        x.append(name_text)
                else:
                    if len(s.activity[plot]) > 0:
                        y.append(len(s.activity[plot]))
                        x.append(name_text)

            trace = go.Box(x=x, y=y, name=key1, boxpoints='all', jitter=0.3, pointpos=-1.8, boxmean='sd')                     #chooses mean plot using box display
            data.append(trace)
        if search_by is None:
            title1 = 'clicks'
        else:
            title1 = plot
        layout = go.Layout(
            yaxis=dict(
                title=title1,
                zeroline=False
            ),
            xaxis=dict(
                title='Grades',
                zeroline=False
            ),
            boxmode='group'
        )
        fig = go.Figure(data=data, layout=layout)
        folder = "Graphs/"
        file_name = folder + self.name + "_agg_plot_" + plot + ".html"
        offline.plot(fig, filename=file_name)

    def no_0s_medians_per_week(self,plot, search_by = None, week_number = None):        #if graphing clicks and days, search_by sould be entered as None
        grades = self.group_by_grade()
        data = []
        deviation = 2
        if week_number is None:
            if not isinstance(plot, str):
                for key, value in grades.items():
                    grades[key] = self.group_by_weeks(grades[key], plot)
            elif search_by is None:
                for key, value in grades.items():
                    grades[key] = self.group_by_weeks(grades[key])           #creates week dictionary with grade in each week
            else:
                self.new_activity(plot, search_by)
                for key, value in grades.items():
                    grades[key] = self.group_by_weeks(grades[key], plot)           #creates week dictionary with grade in each week
            #print('no 0s weeks:')
            for key1, weeks in grades.items():                              #for weeks in each grade
                #print(key1)
                x = []
                y = []
                for key2, l in weeks.items():                               #for grades in each week
                    #print(key2)
                    index = 0
                    raw_y = []
                    for s in l:                                             #for students in each grade
                        if search_by is None:
                            if len(s.clicks) > 0:
                                index+=1
                                raw_y.append(len(s.clicks))
                                #x.append(key2)
                        else:
                            if len(s.activity[plot]) > 0:
                                index+=1
                                raw_y.append(len(s.activity[plot]))
                                #x.append(key2)
                        #y.append(len(s.activity[plot]))
                    y += self.std_filter(raw_y, deviation)
                    x += [key2 for number in range(index)]

                trace = go.Box(x=x, y=y, name=key1, boxmean='sd')                     #chooses mean plot using box display
                data.append(trace)
            if search_by is None:
                title1 = 'clicks'
            else:
                title1 = plot
            layout = go.Layout(
                yaxis=dict(
                    title=title1,
                    zeroline=False
                ),
                xaxis=dict(
                    title='Weeks',
                    zeroline=False
                ),
                boxmode='group'
            )
        else:
            if search_by is None:
                #print("search_by = None")
                for key, value in grades.items():
                    grades[key] = self.group_by_days(week_number, grades[key])
            else:
                for key, value in grades.items():
                    grades[key] = self.group_by_days(week_number, plot)
            #print("no 0s weeks:")
            for key1, weeks in grades.items():              #key1 is week numbers
                x = []
                y = []
                for key2, l in weeks.items():               #key2 is grade groups
                    #print(key2)
                    index = 0
                    raw_y = []
                    for s in l:
                        if search_by is None:
                            if len(s.clicks) > 0:
                                index+=1
                                raw_y.append(len(s.clicks))
                                #x.append(key2)
                        else:
                            if len(s.activity[plot]) > 0:
                                index+=1
                                raw_y.append(len(s.activity[plot]))
                    y += self.std_filter(raw_y, deviation)
                    x += [key2 for number in range(index)]
                        #y.append(len(s.activity[plot]))
                trace = go.Box(x=x, y=y, name=key1, boxmean='sd')
                data.append(trace)
            if search_by is None:
                title1 = 'clicks'
            else:
                title = self.name,
            layout = go.Layout(
                yaxis=dict(
                    title=title1,
                    zeroline=False
                ),
                xaxis=dict(
                    title='Weeks',
                    zeroline=False
                ),
                boxmode='group'
            )
        fig = go.Figure(data=data, layout=layout)
        folder = "Graphs/"
        file_name = folder + "No_0s_" + self.name + "_median_" + plot + ".html"
        offline.plot(fig, filename=file_name)

    def with_0s_medians_per_week(self,plot, search_by = None, week_number = None):        #if graphing clicks and days, search_by sould be entered as None
        grades = self.group_by_grade()
        data = []
        deviation = 2
        if week_number is None:
            if not isinstance(plot, str):
                for key, value in grades.items():
                    grades[key] = self.group_by_weeks(grades[key], plot)
            elif search_by is None:
                for key, value in grades.items():
                    grades[key] = self.group_by_weeks(grades[key])           #creates week dictionary with grade in each week
            else:
                self.new_activity(plot, search_by)
                for key, value in grades.items():
                    grades[key] = self.group_by_weeks(grades[key], plot)           #creates week dictionary with grade in each week
            #print('with 0s weeks:')
            for key1, weeks in grades.items():                              #for each week, plot the students by grade
                x = []
                y = []
                for key2, l in weeks.items():
                    #print(key2)
                    index = 0
                    raw_y = []
                    for s in l:
                        if search_by is None:
                            index +=1
                            raw_y.append(len(s.clicks))
                            #x.append(key2)
                        else:
                            index +=1
                            raw_y.append(len(s.activity[plot]))
                            #x.append(key2)
                    y += self.std_filter(raw_y, deviation)
                    x += [key2 for number in range(index)]
                trace = go.Box(x=x, y=y, name=key1, boxmean='sd')                     #chooses mean plot using box display
                data.append(trace)
            if search_by is None:
                title1 = 'clicks'
            else:
                title1 = plot
            layout = go.Layout(
                yaxis=dict(
                    title=title1,
                    zeroline=False
                ),
                xaxis=dict(
                    title='Weeks',
                    zeroline=False
                ),
                boxmode='group'
            )
        else:
            if search_by is None:
                for key, value in grades.items():
                    grades[key] = self.group_by_days(week_number, grades[key])
            else:
                for key, value in grades.items():
                    grades[key] = self.group_by_days(week_number, plot)
            #print('with 0s weeks:')
            for key1, weeks in grades.items():
                x = []
                y = []
                for key2, l in weeks.items():
                    #print(key2)
                    index = 0
                    raw_y = []
                    for s in l:
                        if search_by is None:
                            index +=1
                            raw_y.append(len(s.clicks))
                            #x.append(key2)
                        else:
                            index +=1
                            raw_y.append(len(s.activity[plot]))
                            #x.append(key2)
                    y += self.std_filter(raw_y, deviation)
                    x += [key2 for number in range(index)]
                trace = go.Box(x=x, y=y, name=key1, boxmean='sd')
                data.append(trace)
            if search_by is None:
                title1 = 'clicks'
            else:
                title = self.name,
            layout = go.Layout(
                yaxis=dict(
                    title=title1,
                    zeroline=False
                ),
                xaxis=dict(
                    title='Weeks',
                    zeroline=False
                ),
                boxmode='group'
            )
        fig = go.Figure(data=data, layout=layout)
        folder = "Graphs/"
        file_name = folder + "With_0s_" + self.name + "_median_" + plot + ".html"
        offline.plot(fig, filename=file_name)

        """aggrigate scatter plot"""

    def awesome_plot(self,plot, search_by = None):
        grades = self.group_by_grade()
        data = []
        weeks = []
        if not isinstance(plot, str):
            for key, value in grades.items():
                grades[key] = self.group_by_weeks(grades[key], plot)
        elif search_by is None:        #plots clicks
            for key, value in grades.items():
                grades[key] = self.group_by_weeks(grades[key])
        else:                       #plots activities
            self.new_activity(plot, search_by)
            for key, value in grades.items():
                grades[key] = self.group_by_weeks(grades[key], plot)
        for i in range(1,len(grades["60's"])+1):
            weeks.append(i)
        # make figure
        figure = {
            #'title': self.name,
            'data': [],
            'layout': {},
            'frames': []
        }
        # fill in most of layout
        figure['layout']['xaxis'] = {'range': [0, 1.1],'title': 'Exam Grade'}
        figure['layout']['hovermode'] = 'closest'
        figure['layout']['title'] =  self.name
        figure['layout']['sliders'] = {
            'args': [
                'transition', {
                    'duration': 400,
                    'easing': 'cubic-in-out'
                }
            ],
            'initialValue': '1',
            'plotlycommand': 'animate',
            'values': weeks,
            'visible': True
        }
        figure['layout']['updatemenus'] = [
            {
                'buttons': [
                    {
                        'args': [None, {'frame': {'duration': 500, 'redraw': False},
                                 'fromcurrent': True, 'transition': {'duration': 300, 'easing': 'quadratic-in-out'}}],
                        'label': 'Play',
                        'method': 'animate'
                    },
                    {
                        'args': [[None], {'frame': {'duration': 0, 'redraw': False}, 'mode': 'immediate',
                        'transition': {'duration': 0}}],
                        'label': 'Pause',
                        'method': 'animate'
                    }
                ],
                'direction': 'left',
                'pad': {'r': 10, 't': 87},
                'showactive': False,
                'type': 'buttons',
                'x': 0.1,
                'xanchor': 'right',
                'y': 0,
                'yanchor': 'top'
            }
        ]

        sliders_dict = {
            'active': 0,
            'yanchor': 'top',
            'xanchor': 'left',
            'currentvalue': {
                'font': {'size': 20},
                'prefix': 'Week:',
                'visible': True,
                'xanchor': 'right'
            },
            'transition': {'duration': 300, 'easing': 'cubic-in-out'},
            'pad': {'b': 10, 't': 50},
            'len': 0.9,
            'x': 0.1,
            'y': 0,
            'steps': []
        }
        # make data
        week = 1
        linear_x = []
        linear_y = []
        y_range = 0
        for key1, weeks1 in grades.items():
            x = []
            y = []
            no_zero_y = []
            #no_zero_x = []
            names = []
            size = []
            average = 0
            for s in weeks1[week]:
                if not isinstance(plot, str):
                    y.append(len(s.activity["plot_list"]))
                    if len(s.activity["plot_list"]) > 0:
                        no_zero_y.append(len(s.activity["plot_list"]))
                elif search_by is None:
                    #print(len(s.activity))
                    #for key, a in s.activity.items():
                        #print("key: ",key)
                        #print("list: ", a)
                        #print("------")
                    #print("done looping through dict")
                    y.append(len(s.activity[plot]))
                    if len(s.activity[plot]) > 0:
                        no_zero_y.append(len(s.activity[plot]))
                        #no_zero_x.append(s.rolling_grade[week-1])
                else:
                    self.new_activity(plot, search_by)
                    y.append(len(s.activity[plot]))
                    if len(s.activity[plot]) > 0:
                        no_zero_y.append(len(s.activity[plot]))
                        #no_zero_x.append(s.rolling_grade[week-1])
                if y[-1] > y_range:
                    y_range = y[-1]
                names.append(s.name)
                size.append(20)
                #if len(s.rolling_grade) > 10:
                x.append(s.rolling_grade[week-1])
            linear_x += x
            linear_y += y
            #regr = linear_model.LinearRegression()
            #regr.fit(x, y)

            if len(y) < 1:
                y.append(0)
            else:
                y.append(sum(y)/len(y))
            if len(x) < 1:
                x.append(0)
            else:
                x.append(sum(x)/len(x))
            size.append(800)
            names.append("Average" + "<br> N=" + str(len(y)-1))
            if len(no_zero_y) < 1:
                y.append(0)
            else:
                y.append(sum(no_zero_y)/len(no_zero_y))
            x.append(x[-1])
            if len(y) < 2:
                size.append(0)
                ave_name = "No 0's Average: " + str(0) + " % were active"
            else:
                size.append(800*len(no_zero_y)/(len(y)-2))
                ave_name = "No 0's Average: " + str(round(100*len(no_zero_y)/(len(y)-2),2)) + " % were active"
            names.append(ave_name)
                #else:
                #    y.append(s.grade)
            data_dict = go.Scatter(
                #title : self.name,
                x = x,          #list(dataset_by_year_and_cont['lifeExp'])
                y = y,         #dataset_by_year_and_cont['gdpPercap']
                mode =  'markers',
                text = names,
                marker = {'sizemode': 'area', 'size': size},
                name = key1
                #'size': size
            )
            figure['data'].append(data_dict)
        slope, intercept, r_value, p_value, std_err = stats.linregress(linear_x,linear_y)
        line = []
        for l in linear_x:
            line.append(slope*l+intercept)
        linear_fit = go.Scatter(
            #title : self.name,
            x =  linear_x,          #list(dataset_by_year_and_cont['lifeExp'])
            y = line,         #dataset_by_year_and_cont['gdpPercap']
            mode = 'lines',
            #'text': names,
            #'marker': {'sizemode': 'area', 'size': size},
            name = "Linear Fit " + "P value: "+ str(p_value),
            #'size': size
        )
        figure['data'].append(linear_fit)
        # make frames
        for week in weeks:
            linear_x = []
            linear_y = []
            frame = {'data': [], 'name': str(week)}
            for key1, weeks2 in grades.items():
                no_zero_y = []
                #no_zero_x = []
                x = []
                y = []
                names = []
                size = []
                for s in weeks2[week]:
                    if search_by is None:
                        y.append(len(s.activity[plot]))
                        if len(s.activity[plot]) > 0:
                            no_zero_y.append(len(s.activity[plot]))
                            #no_zero_x.append(s.rolling_grade[week-1])
                    else:
                        self.new_activity(plot, search_by)
                        y.append(len(s.activity[plot]))
                        if len(s.activity[plot]) > 0:
                            no_zero_y.append(len(s.activity[plot]))
                            #no_zero_x.append(s.rolling_grade[week-1])
                    names.append(s.name)
                    size.append(20)
                    #if len(s.rolling_grade) > 10:                #not sure why out of range, fix bug later
                    #print(s.rolling_grade[week-1])
                    if len(s.rolling_grade) < week:
                        print(s.name, s.rolling_grade)
                    else:
                        x.append(s.rolling_grade[week-1])
                    if y[-1] > y_range:
                        y_range = y[-1]
                linear_x += x
                linear_y += y
                y.append(sum(y)/len(y))
                x.append(sum(x)/len(x))
                size.append(800)
                names.append("Average" + "<br> N=" + str(len(y)-1))
                if len(no_zero_y) > 0:
                    y.append(sum(no_zero_y)/len(no_zero_y))
                else:
                    y.append(0)
                x.append(x[-1])
                size.append(800*len(no_zero_y)/(len(y)-2))
                ave_name = "No 0's Average: " + str(round(100*len(no_zero_y)/(len(y)-2),2)) + " % were active"
                names.append(ave_name)
                    #    print(s.name)
                    #else:
                    #    y.append(s.grade)
                slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
                #print(slope)
                #print(intercept)
                #print(x)
                line = []

                data_dict = go.Scatter(
                    #title : self.name,
                    x = x,          #list(dataset_by_year_and_cont['lifeExp'])
                    y = y,         #dataset_by_year_and_cont['gdpPercap']
                    mode =  'markers',
                    text = names,
                    marker = {'sizemode': 'area', 'size': size},
                    name = key1
                    #'size': size
                )
                frame['data'].append(data_dict)
            slope, intercept, r_value, p_value, std_err = stats.linregress(linear_x,linear_y)
            line = []
            for l in linear_x:
                line.append(slope*l+intercept)
            linear_fit = go.Scatter(
                #title : self.name,
                x =  linear_x,          #list(dataset_by_year_and_cont['lifeExp'])
                y = line,         #dataset_by_year_and_cont['gdpPercap']
                mode = 'lines',
                #'text': names,
                #'marker': {'sizemode': 'area', 'size': size},
                name = "Linear Fit " + "P value: "+ str(p_value),
                #'size': size
            )
            frame['data'].append(linear_fit)
            figure['frames'].append(frame)
            slider_step = {'args': [
                [week],
                {'frame': {'duration': 300, 'redraw': False},
                 'mode': 'immediate',
               'transition': {'duration': 300}}
             ],
             'label': str(week) + "<br> P-value: "+ '%.2E'%Decimal(p_value),
             'method': 'animate'}
            sliders_dict['steps'].append(slider_step)
        figure['layout']['sliders'] = [sliders_dict]
        if not isinstance(plot, str):
            figure['layout']['yaxis'] = {'range': [0, y_range+10],'title': 'Activities'}
        else:
            figure['layout']['yaxis'] = {'range': [0, y_range+10],'title': 'Activity: '+ plot}
        folder = "Graphs/"
        file_name = folder + self.name + "_scatter_" + plot + ".html"
        offline.plot(figure, filename=file_name)

    def agg_scatter_plot(self,plot, search_by = None):
        x = []
        y = []
        x_max = 0
        if search_by is not None:
            self.new_activity(plot, search_by)
        for s in self.students:
            #name_text = key1 + "<br> N=" + str(len(students)) #<br> is an html line break since plotly is html based
            if not isinstance(plot, str):
                activity_list = s.concat(plot)
                if len(activity_list) > 0:
                    if s.exams[-1] > 0:
                        x.append(len(activity_list))
                        y.append(s.grade)
            else:
                if len(s.activity[plot]) > 0:
                    if s.exams[-1] > 0:
                        x.append(len(s.activity[plot]))
                        y.append(s.grade)
        # Generated linear fit
        slope, intercept, r_value, p_value, std_err = stats.linregress(x,y)
        line = []
        for l in x:
            line.append(slope*l+intercept)
        # Creating the dataset, and generating the plot
        """
        x1 = np.asarray(x)
        y1 = np.asarray(y)
        rg=sns.regplot(x1,y1)

        X=rg.get_lines()[0].get_xdata()         # x-coordinate of points along the regression line
        Y=rg.get_lines()[0].get_ydata()         # y-coordinate
        P=rg.get_children()[1].get_paths()      #The list of Path(s) bounding the shape of 95% confidence interval-transparent
        p_codes={1:'M', 2: 'L', 79: 'Z'}        #dict to get the Plotly codes for commands to define the svg path
        path=''
        for s in P[0].iter_segments():
            c=p_codes[s[1]]
            xx, yy=s[0]
            path+=c+str('{:.5f}'.format(xx))+' '+str('{:.5f}'.format(yy))

        shapes=[dict(type='path',
                        path=path,
                        line=dict(width=0.1,color='rgba(68, 122, 219, 0.25)' ),
                        fillcolor='rgba(68, 122, 219, 0.25)')]
        """
        trace1 = go.Scatter(
                        x=x,
                        y=y,
                        mode='markers',
                        marker=go.Marker(color='rgb(255, 0, 0)'),
                        name='Data'
                        )

        trace2 = go.Scatter(
                        x=x,
                        y=line,
                        mode='lines',
                        marker=go.Marker(color='rgb(31, 119, 180)'),
                        name='Fit'
                        )
        if not isinstance(plot, str):
                plot = ' '.join(plot)
        layout = go.Layout(
                        title= "<b>" + self.name + "</b>" + "<br> P-value: "+ '%.2E'%Decimal(p_value),
                        yaxis = {"range": [0,1],'title': 'Grade'},
                        xaxis = {'title': 'Activity: '+ plot, 'range': [0, max(x)]},
                        #plot_bgcolor='rgb(229, 229, 229)',
                        #xaxis=go.XAxis(zerolinecolor='rgb(255,255,255)', gridcolor='rgb(255,255,255)'),
                        #yaxis=go.YAxis(zerolinecolor='rgb(255,255,255)', gridcolor='rgb(255,255,255)'),
                        #shapes=shapes,
                        )
        #print(layout['xaxis']['range'])
        data = [trace1, trace2]
        fig = go.Figure(data=data, layout=layout)
        folder = "Graphs/"
        file_name = folder + "Agg_Scatter_" + self.name + "_" + plot + ".html"
        offline.plot(fig, filename=file_name)


#graph exams grades 15/15/35
#graph final grade
"""
average w/ 0s: done
w/out 0s: done
median w/out 0s: done
percent of 0s per grade group: done
"""

def data_to_plotly(x):
    k = []
    for i in range(0, len(x)):
        k.append(x[i][0])
    return k

def update_data(terms):
    with open("fall_winter_2018.file", "wb") as f:
        pickle.dump(terms, f, pickle.HIGHEST_PROTOCOL)
    print("done updating terms")

def get_term(terms):
    term_list = ""
    print("Welcome to the PH20X course database.")
    print("The terms available are:")
    for l in range(len(terms)):
        term_list += terms[l].name
        if l < len(terms)-1:
            term_list += ", "
    print(term_list)
    while 1:
        selected_term = input("Please enter a term listed above:")
        for t in terms:
            print(t.name, selected_term)
            if t.name in selected_term:
                return t
        print("that is not a correct entry")

def create_new_act(term):
    act_name = input("Enter the dataset name.")
    search_by = input("Enter the dataset search parameter.")
    print("Your available graphs are:")
    print("aggrigate, median w/ 0's, median w/out 0's, scatter")
    plot = input("select one or type 'all'")
    if "agg" in plot:
        term.plot_agg(act_name,search_by)
        return
    elif "median w/ 0's" in plot:
        term.with_0s_medians_per_week(act_name,search_by)
        return
    elif "median w/out 0's" in plot:
        term.no_0s_medians_per_week(act_name,search_by)
        return
    elif "scatter" in plot:
        term.awesome_plot(act_name,search_by)
        return
    elif "all" in plot:
        term.plot_agg(act_name,search_by)
        term.with_0s_medians_per_week(act_name,search_by)
        term.no_0s_medians_per_week(act_name,search_by)
        term.awesome_plot(act_name,search_by)
        return

def get_activities(term):
    all = input("Do you want to combine some or all activities?")
    if "all" in all:
        return ["all"]
    elif "some" in all:
        datasets = term.check_activity(input("Enter each dataset and separate with a ' ' "))
        return datasets

def get_resp(term):
    while 1:
        act_list = get_activities(term)
        print("Your available graphs are:")
        print("aggrigate, median w/ 0's, median w/out 0's, scatter")
        plot = input("select one or type 'all'")
        if "agg" in plot:
            term.plot_agg(act_list)
            return
        elif "median w/ 0's" in plot:
            term.with_0s_medians_per_week(act_list)
            return
        elif "median w/out 0's" in plot:
            term.no_0s_medians_per_week(act_list)
            return
        elif "scatter" in plot:
            term.awesome_plot(act_list)
            return
        elif "all" in plot:
            term.plot_agg(act_list)
            term.with_0s_medians_per_week(act_list)
            term.no_0s_medians_per_week(act_list)
            term.awesome_plot(act_list)
            return

"""To prepare data files, ensure first row is column names"""
"""ensure grades are all from 0-1, not 0-100"""

def load_files():
    #'spring','04/03/2017','06/15/2017'
    #'winter', '01/09/2017', '03/25/2017'
    #'fall','09/25/2016','12/11/2016'    doesnt include week 0
    f1 = course('Fall_2017','09/25/2017','12/11/2017')
    w1 = course('Winter_2018', '01/08/2018', '03/26/2018')
    s1 = course('spring','04/02/2018','06/15/2018')

    #'ph201_F16_Anon_Grade.xlsx'
    #'ph202_w17_grades_boxsand-anon.xlsx'
    #'PH203-grade-book-deidentified.xlsx'
    #file0 = pd.read_excel('BoxSand_videos_Daily_Learning_Guide.xlsx')   #for later use in AI algorithm
    file1 = pd.read_excel('ANON-ph201_f17_grades.xlsx')         #doesnt work for 202 due to 8 hw grades instead of 6
    file3 = pd.read_excel('ANON-ph202_w18_grades.xlsx')
    file5 = pd.read_excel('PH203-S18-grades-NONAME.xlsx')
    file7 = pd.read_excel('ph203_s18_rawdata.xlsx')           #imports duedates

    #'ph201_F16_Anon_BS_Data.xlsx'
    #'BoxSand-WS2017.xlsx'
    file2 = pd.read_excel('ph201_f17_rawdata.xlsx')
    file4 = pd.read_excel('ph202_w18_rawdata.xlsx')
    #file6 = pd.read_excel(file0,'PH 201 Fall 2016')             #imports duedates
    #file7 = pd.read_excel(file0,'PH 203 Spring 2017')           #imports duedates

    f1.add_students(file1, file2)
    w1.add_students(file3, file4)
    s1.add_students(file5, file7)
    terms = [f1, w1, s1]
    #s1.add_students(file5, file4)
    with open("fall_winter_2018.file", "wb") as f:
        pickle.dump(terms, f, pickle.HIGHEST_PROTOCOL)
    print("done loading file")

def retrieve_data():
    with open("fall_winter_2018.file", "rb") as f:
        dump = pickle.load(f)
    return dump

def run():
    terms = retrieve_data()
    cont = 1
    while cont is 1:
        term = get_term(terms)
        activities = ""
        for l in range(len(term.activities)):
            activities += term.activities[l]
            if l < len(term.activities)-1:
                activities += ", "
        print("The currently available data sets are:")
        print(activities)
        response = input("Would you like to create a new dataset?")
        if "y" in response:
            create_new_act(term)
            update_data(terms)
        else:
            get_resp(term)
            update_data(terms)
        end_con = input("Do you wish to graph another activity?")
        if "n" in end_con:
            cont = 0

def bypass():
    terms = retrieve_data()
    f1 = terms[0]
    w1 = terms[1]
    s1 = terms[2]
    #for key, act in s1.students[1].activity.items():
        #print("Key: ",key)
        #print("list: ",act)

    s1.agg_scatter_plot("solutions","sol")
    s1.agg_scatter_plot("videos(finished)", "FINISHED")
    s1.agg_scatter_plot("videos", "media")
    plots = ["solutions","videos"]
    s1.agg_scatter_plot(plots)
    update_data(terms)

#load_files()
#run()
bypass()
