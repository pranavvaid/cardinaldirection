import requests
import xmltodict
from datetime import datetime

BASEURL = "https://explorecourses.stanford.edu/"
DEPARTMENTURLMODIFER = "?view=xml-20140630"
COURSEURLMODIFIER = "search?view=xml-20140630&academicYear=&q={DEPARTMENT}&filter-departmentcode-{DEPARTMENT}=on&filter-coursestatus-Active=on"

# This function retrieves the all departments
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

def retrieveDepartmentCourses(departmentName):
    departmentCourseModifier = COURSEURLMODIFIER.format(DEPARTMENT=departmentName)
    r = requests.get(BASEURL+departmentCourseModifier)
    entireCourseData = xmltodict.parse(r.text, force_list = ('course'))
    importantCourseData = []
    if entireCourseData['xml']['courses'] is None:
        return importantCourseData
    for course in entireCourseData['xml']['courses']['course']:
        importantData = {key:course[key] for key in course.keys() & {'title', 'description', 'unitsMin', 'unitsMax', 'subject', 'code'}}
        importantCourseData.append(importantData)
    return importantCourseData

def findPrerequisiteString(courseDescription):
    if courseDescription is None:
        return ""
    preReqKeyPhrases = ["Prerequisites", "Prerequisite"]
    keyPhraseLen = 0
    for keyPhrase in preReqKeyPhrases:
        prereqIndex = courseDescription.find(keyPhrase)
        if prereqIndex != -1:
            keyPhraseLen = len(keyPhrase)
            break
    if prereqIndex == -1:
        return ""
    endPrereqIndex = courseDescription.find(".", prereqIndex)
    if endPrereqIndex != -1:
        prerequisiteString = courseDescription[prereqIndex+keyPhraseLen:endPrereqIndex]
    else:
        prerequisiteString = courseDescription[prereqIndex+keyPhraseLen:]
    return prerequisiteString


def extractClassNames(str, departmentCode, allDepartments):
    if str is None:
        return
    latestDepartment = departmentCode
    currentlyBuildingDepartment = False
    latestNumber = ""
    currentlyBuildingNumber = False
    allClasses = [];
    i = 0
    while i < len(str):
        if str[i].isdigit():
            if not currentlyBuildingNumber:
                latestNumber = str[i]
                currentlyBuildingNumber = True
            else:
                latestNumber+=str[i]
            if i+1 == len(str):
                newClass = latestDepartment + latestNumber
                if newClass not in allClasses:
                    allClasses.append(newClass)
        else:
            if currentlyBuildingNumber:
                # Some courses might have a number in their code
                for j in range (i, len(str)):
                    if str[j].isalpha():
                        latestNumber += str[j]
                    else:
                        i = j-1
                        break
                newClass = latestDepartment + latestNumber
                if newClass not in allClasses:
                    allClasses.append(newClass)
            currentlyBuildingNumber = False
        
        if str[i].isupper():
            newDepartmentName = ""
            for d in allDepartments:
                possDepCode = d['name']
                possDepFullName = d['longname']
                if len(possDepCode) > len(newDepartmentName) and i+len(possDepCode) <= len(str) and str[i:i+len(possDepCode)] == possDepCode:
                    newDepartmentName = possDepCode
                if len(possDepFullName) > len(newDepartmentName) and i+len(possDepFullName) <= len(str) and str[i:i+len(possDepFullName)] == possDepFullName:
                    newDepartmentName = possDepFullName
            if newDepartmentName != "":
                i = i + len(newDepartmentName)
                currentDepartment = newDepartmentName
        '''
        if str[i].isupper():
            if not currentlyBuildingDepartment:
                latestDepartment = str[i]
                currentlyBuildingDepartment = True
            else:
                latestDepartment += str[i]
        else:
            if currentlyBuildingDepartment and str[i].isalpha():
                for j in range (i, len(str)):
                    if str[j].isalpha():
                        latestDepartment += str[j]
                    else:
                        i = j-1
                        break
            currentlyBuildingDepartment = False
        '''
        i = i + 1
    print(allClasses)
    
print("RETRIEVING DEPARTMENTS")
d = retrieveDepartments()
allCourses = [];

for department in d:
    print("RETRIEVING DEPARTMENT COURSES FOR " + department['name'] + " AT " + datetime.now().strftime('%H:%M:%S'))
    toAdd = retrieveDepartmentCourses(department['name'])
    if(department['name'] == 'EEES'):
        break
    if toAdd is not None:
        allCourses.extend(toAdd)
for course in allCourses:
    print("")
    print("----------------------------------------------------------------")
    print(course['title'])
    print("")
    print(course['description'])
    preReq = findPrerequisiteString(course['description']);
    print("")
    print(preReq)
    print("")
    extractClassNames(preReq, course['subject'], d)
    print("----------------------------------------------------------------")

