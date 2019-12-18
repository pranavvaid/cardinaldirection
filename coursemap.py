from stanfordclasses import StanfordClass
import pickle
import networkx as nx

with open('stanfordclasslist.pkl', 'rb') as f:
    StanfordClassList = pickle.load(f)
f.close()

departmentsToGraph = set([])
depfile = open('departmentstograph.txt', 'r')
line = depfile.readline()
while line:
    departmentsToGraph.add(line.strip())
    line = depfile.readline()
depfile.close()

coursemap = nx.DiGraph()
coursesInGraph = set([])
for stanfordCourse in StanfordClassList:
    courseName = stanfordCourse.name
    courseDepartment = courseName[:courseName.find(" ")]
    if courseDepartment in departmentsToGraph:
        if (stanfordCourse.prerequisites is None or len(stanfordCourse.prerequisites) == 0) and (stanfordCourse.prereqsOf is None or len(stanfordCourse.prereqsOf) == 0):
            continue
        coursesInGraph.add(stanfordCourse)
        courseDescription = stanfordCourse.description
        if courseDescription is None:
            courseDescription = ""
        coursemap.add_node(stanfordCourse, department=courseDepartment, name=courseName, title=stanfordCourse.title, description=courseDescription)
    
for course in coursesInGraph:
    for preReq in course.prerequisites:
        if preReq in coursesInGraph:
            prereqCourseName = preReq.name
            prereqCourseDepartment = prereqCourseName[:prereqCourseName.find(" ")]
            endCourseName = course.name
            endCourseDepartment = endCourseName[:endCourseName.find(" ")]
            coursemap.add_edge(preReq, course, same_department=(endCourseDepartment==prereqCourseDepartment))

nx.write_gexf(coursemap, '/pickles/coursemap.gexf')
