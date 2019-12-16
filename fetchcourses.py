import requests
import xmltodict

BASEURL = "https://explorecourses.stanford.edu/"
DEPARTMENTURLMODIFER = "?view=xml-20140630"
COURSEURLMODIFIER = "search?view=xml-20140630&academicYear=&q={DEPARTMENT}&filter-departmentcode-{DEPARTMENT}=on&filter-coursestatus-Active=on"

def retrieveDepartments():
    allDepartments = []
    r = requests.get(BASEURL+DEPARTMENTURLMODIFER)
    courseDictionary = xmltodict.parse(r.text, force_list = ('school', 'department'))
    for school in courseDictionary['schools']['school']:
        for department in school['department']:
            currentDepartment = {
                'name': department['@name'],
                'longname' : department['@longname'],
                'school' : school['@name']
            }
            allDepartments.append(currentDepartment)
    return allDepartments

def retriveDepartmentCourses(departmentName):
    departmentCourseModifier = COURSEURLMODIFIER.format(DEPARTMENT=departmentName)
    r = requests.get(BASEURL+departmentCourseModifier)
    entireCourseData = xmltodict.parse(r.text, force_list=('course'))
    print(entireCourseData)


d = retrieveDepartments()
for department in d:
    retriveDepartmentCourses(department['name'])
