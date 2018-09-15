import csv
import pandas as pd
import re
import time
from datetime import*
from collections import*
from itertools import filterfalse
import plotly.offline as offline
import plotly.graph_objs as go


class student(object):              #defining student class
    """docstring for student."""
    def __init__(self, name):
        self.name = name
        self.exams = []
        self.hw =    []
        self.grade = 0
        #self.clicks = []
        self.videos = []            #when filled, will be a list of lists
        self.weeks = {}             #fillled when in course
    def add_exam(self, arg):
        self.exams.append(arg)

    def add_hw(self, arg):
        self.hw.append(arg)

    def add_video(self, arg, arg1):
        d = datetime.strptime(arg1, '%m/%d/%Y - %H:%M').date()      #store as a date data type
        list1 = [arg, d]
        self.videos.append(list1)


class course(object):
    """docstring for course."""
    def __init__(self, name, start_date, end_date):
        self.name = name
        self.start_date = datetime.strptime(start_date, '%m/%d/%Y').date()
        self.end_date = datetime.strptime(end_date, '%m/%d/%Y').date()
        self.students = []

    def in_course(self, arg):
        if self.start_date > arg[1] < self.end_date:
            return True
        else:
            return False

    def add_students(self, student):
        week = timedelta(weeks = 1)
        #weeks = list(range(1,12))                              #list from 1-11 for course weeks
        for s in student:                                       #for each student
            s.videos[:] = filterfalse(self.in_course,s.videos)  #removes videos out of course timeline
            for v in s.videos:                                  #for each video
                for w in range(1,12):                           #assigns the video a course week
                    if (self.start_date + w*week) > v[1] >= (self.start_date + (w-1)*week):
                        v.append(w)
            self.students.append(s)                             #adds the student

    def group_by_grade(self, weeks = None):
        grades = {"40's":[], "50's":[],"60's":[],"70's":[],"80's":[],"90's":[]}
        grades = OrderedDict(sorted(grades.items(), key=lambda t: t[0]))        #sorted by keys
        if weeks is None:
            for s in self.students:
                i=.5
                for key in grades:
                    if s.grade < i and s.grade >= (i-.1):
                        grades[key].append(s)
                    i+=.1
        else:
            for s in weeks:
                i=.5
                for key1 in grades:
                    if s.grade < i and s.grade >= (i-.1):
                        grades[key1].append(s)
                    i+=.1
        return grades

    def median_videos_per_week(self):
        grades = self.group_by_grade()
        data = []
        for key, value in grades.items():
            grades[key] = self.group_by_weeks(grades[key])
        for key1, weeks in grades.items():
            x = []
            y = []
            for key2, l in weeks.items():
                for s in l:
                    y.append(len(s.videos))
                    x.append(key2)
            trace = go.Box(x=x, y=y, name=key1)
            data.append(trace)
        layout = go.Layout(
            yaxis=dict(
                title='Videos Watched',
                zeroline=False
            ),
            boxmode='group'
        )
        fig = go.Figure(data=data, layout=layout)
        offline.plot(fig)


    def group_by_weeks(self, grades = None):           #creating another dictionary is more expensive but easier to troubleshoot
        weeks = {}
        for r in range(1,12):           #creates weeks dictionary
            weeks[r] = []
        if grades is None:
            for key in weeks:
                for s in self.students:
                    temp = student(s.name)
                    temp.grade = s.grade
                    for v in s.videos:
                        if v[2] == key:
                            temp.videos.append(v)
                    weeks[key].append(temp)
                weeks[key] = self.group_by_grade(weeks[key])
        else:
            for key in weeks:
                for s in grades:
                    temp = student(s.name)
                    temp.grade = s.grade
                    for v in s.videos:
                        if v[2] == key:
                            temp.videos.append(v)
                    weeks[key].append(temp)
        return weeks

#fall[6] = ['ph201_F16_Anon_Grade.csv','encoding="utf8"','ph201_F16_Anon_BS_Data.csv','encoding="utf8"','fall','09/25/2016','12/11/2016']
#spring[5] = ['PH203-grade-book-deidentified.csv','BoxSand-WS2017.csv','spring','04/03/2017','05/01/2017']

#'PH203-grade-book-deidentified.csv'
#'ph201_F16_Anon_Grade.csv',encoding="utf8"
with open('ph201_F16_Anon_Grade.csv',encoding="utf8") as file :        #doesnt work for 202 due to 8 hw grades instead of 6
    reader = csv.reader(file)
    student_list =[]
    next(file)                                      #skip header
    for row in reader:
        x = student(row[1])                         # initializes a student class with student name in column 2
        for i in range(10,(len(row)-13)):           #start at column 10 ends at 16(had to use row so it knows what to iterate)
            if row[i] ==' ':                        #just in case someone forgets to enter a grade
                row[i] = 0
            x.hw.append(float(row[i]))
        for j in range(17,(len(row)-6),2):          #start at column 17 ends at 23(had to use row so it knows what to iterate) reads every 2 columns
            if row[j] ==' ':                        #just in case someone forgets to enter a grade
                row[j] = 0
            x.add_exam(float(row[j]))
        if row[25] ==' ':                           #just in case someone forgets to enter a grade
            row[25] = 0
        x.grade = float(row[25])

        student_list.append(x)

#'BoxSand-WS2017.csv'
#'ph201_F16_Anon_BS_Data.csv',encoding="utf8"
with open('ph201_F16_Anon_BS_Data.csv',encoding="utf8") as file1:
    reader1 = csv.reader(file1)
    next(file1)
    i=0
    for row in reader1:                                     #checks each row in the file
        if student_list[i].name == row[0]:                  #checks if the student name is correct
            if 'media' in row[1]:                           #'media' identifies it as a video watched
                student_list[i].add_video(row[1],row[3])
        else:
            if (i+1) < len(student_list):
                if student_list[i+1].name == row[0]:        #checks if the next student name is correct
                    i+=1
                    if 'media' in row[1]:
                        student_list[i].add_video(row[1],row[3])
                else:
                    next(file1)                     #if the next student name isnt correct, then it's a student without a grade and all these lines must be skipped

    #'spring','04/03/2017','06/15/2017'
    #'fall','09/25/2016','12/11/2016'    doesnt include week 0
    w1 = course('fall','09/25/2016','12/11/2016')
    w1.add_students(student_list)
    #grade = w1.group_by_grade()
    #weeks = w1.group_by_weeks()
    w1.median_videos_per_week()
