import requests
import xmltodict
from datetime import datetime
import time
from stanfordclasses import StanfordClass
import pickle

BASEURL = "https://explorecourses.stanford.edu/"
DEPARTMENTURLMODIFER = "?view=xml-20140630"
COURSEURLMODIFIER = "search?view=xml-20140630&academicYear=&q={DEPARTMENT}&filter-departmentcode-{DEPARTMENT}=on&filter-coursestatus-Active=on"
numDirectCourseRelations = 0
numIndirectCourseRelations = 0

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
    preReqKeyPhrases = ["Prerequisites", "Prerequisite", "Pre-requisite", "Prerequsite"]
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
                newClass = latestDepartment + " " + latestNumber
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
                newClass = latestDepartment + " " + latestNumber
                if newClass not in allClasses:
                    allClasses.append(newClass)
            currentlyBuildingNumber = False
        
        if str[i].isupper():
            newDepartmentName = ""
            nameToCodeConversion = ""
            for d in allDepartments:
                possDepCode = d['name']
                possDepFullName = d['longname']
                if len(possDepCode) > len(newDepartmentName) and i+len(possDepCode) <= len(str) and str[i:i+len(possDepCode)].upper() == possDepCode.upper():
                    newDepartmentName = possDepCode
                    nameToCodeConversion = ""
                if len(possDepFullName) > len(newDepartmentName) and i+len(possDepFullName) <= len(str) and str[i:i+len(possDepFullName)].upper() == possDepFullName.upper():
                    newDepartmentName = possDepFullName
                    nameToCodeConversion = possDepCode
            if newDepartmentName != "":
                i = i + len(newDepartmentName) - 1
                if nameToCodeConversion != "":
                    latestDepartment = nameToCodeConversion
                else:
                    latestDepartment = newDepartmentName
                
        i = i + 1
    return allClasses

def findAllCourses(departmentNames):
    allCourses = []
    for department in departmentNames:
        print("RETRIEVING DEPARTMENT COURSES FOR " + department['name'] + " AT " + datetime.now().strftime('%H:%M:%S'))
        toAdd = retrieveDepartmentCourses(department['name'])
        if toAdd is not None:
            allCourses.extend(toAdd)
    return allCourses

def createCourseMap(allCourses, allDepartments):
    StanfordClassList = []
    allClassTitles = set([c['subject'] + " " + c['code'] for c in allCourses])
    usedClassTitles = set([])
    # For each course
    for course in allCourses:
        preReqString = findPrerequisiteString(course['description'])
        preReqClasses = extractClassNames(preReqString, course['subject'], allDepartments)
        currentCourse = next((x for x in StanfordClassList if x.name == course['subject'] + " " + course['code']), None)
        # If there is no course currently in the list with this course's name create a new course, otherwise just update the variables of the existing course
        if currentCourse is None:
            currentCourse = StanfordClass(course['title'], course['description'], course['unitsMin'], course['unitsMax'], course['subject'] + " " + course['code'], [], [])
        else:
            currentCourse.title = course['title']
            currentCourse.description = course['description']
            currentCourse.minUnits = course['unitsMin']
            currentCourse.maxUnits = course['unitsMax']
        # For each prequisite class for this course
        for preReq in preReqClasses:
            # If the detected prereq isn't a valid class, then ignore it
            if preReq not in allClassTitles:
                continue
            # Find if a class object has already been created for this prereq
            preReqClassObject = next((x for x in StanfordClassList if x.name == preReq), None)
            if preReqClassObject is None:
                preReqClassObject = StanfordClass("TEMPHOLDER", "TEMPHOLDER", -1, -1, preReq, [], [])
                StanfordClassList.append(preReqClassObject)
            global numDirectCourseRelations
            global numIndirectCourseRelations
            numDirectCourseRelations = numDirectCourseRelations + 2
            numIndirectCourseRelations = numIndirectCourseRelations + 2 + len(preReqClassObject.prerequisites)
            preReqClassObject.prereqsOf.append(currentCourse)
            currentCourse.prerequisites.append(preReqClassObject)
        StanfordClassList.append(currentCourse)
    return StanfordClassList

def retrieveClass(classlist, classTitle = "", className = ""):
    if className != "":
        className = className.replace(" ", "")
        return next((x for x in classlist if x.name.upper().replace(" ", "") == className.upper()), None)
    if classTitle != "":
        return next((x for x in classlist if x.title.upper() == classTitle.upper()), None)
    return None


def list_contains(sublist, mainlist):
    if all(x in mainlist for x in sublist):
        return True
    return False

def determineFutureClasses(completedClassesList, StanfordClassList):
    possibleFutureClasses = set([])
    for completedClass in completedClassesList:
        classToCheck = retrieveClass(StanfordClassList, className = completedClass)
        if classToCheck is not None:
            possibleFutureClasses.update(classToCheck.prereqsOf)
    actualFutureClasses = set([])
    for possibleFutureClass in possibleFutureClasses:
        preReqsOfFutureClass = possibleFutureClass.prerequisites
        if list_contains([c.name for c in preReqsOfFutureClass], completedClassesList):
            actualFutureClasses.add(possibleFutureClass)
    return actualFutureClasses

def determineAllNonPrerequisiteCourses(StanfordClassList):
    futureClasses = set([])
    for possibleClass in StanfordClassList:
        if len(possibleClass.prerequisites) == 0:
            futureClasses.add(possibleClass)
    return futureClasses

def determineAllRequiredPrerequisites(classToDetermine):
    allRequiredClasses = set([])
    if (classToDetermine.prerequisites is None) or len(classToDetermine.prerequisites) == 0 :
        return allRequiredClasses
    for preReqCourse in classToDetermine.prerequisites:
        allRequiredClasses.add(preReqCourse)
        allRequiredClasses.update(determineAllRequiredPrerequisites(preReqCourse))
    return allRequiredClasses

print("RETRIEVING DEPARTMENTS")
allDepartments = retrieveDepartments()
allCourses = findAllCourses(allDepartments)

parseStartTime = time.time()
StanfordClassList = createCourseMap(allCourses, allDepartments)
totalTime = time.time()-parseStartTime
print("COURSE EXTRACTION AND TEXT PROCESSING COMPLETE")
print("Processed the text of " + str(len(allCourses)) + " course descriptions and discovered " + str(numDirectCourseRelations) + " direct relationships and " + str(numIndirectCourseRelations) + " indirect relationships between courses in " + str(totalTime) + " seconds!.")

print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("")
print("WELCOME TO CARDINAL DIRECTION, LET'S HELP YOU FIND WHAT PATHS YOUR COURSES CAN TAKE YOU!")
input("PRESS ENTER TO BEGIN USING THE PROGRAM: ")
for department in allDepartments:
    print("RETRIEVED DEPARTMENT COURSES FOR " + department['name'])
    time.sleep(.002)
print("")
print("")

print("")
print("")
print("WELCOME TO CARDINAL DIRECTION, LET'S HELP YOU FIND WHAT PATHS YOUR COURSES CAN TAKE YOU!")
print("-------------------------------------------------------------------------------------------------------------------------")
while True:
    print("=============================================================================")
    print("What would you like to do?")
    print("1: Retrieve path information about a course.")
    print("2: Help me find what courses I can take.")
    print("3: I'd like to know all the classes I have to take before a certain course")
    print("4: Print out course catalog with path information")
    print("5: Show me all courses with no required prequisites")
    print("6: Quit program")
    print("=============================================================================")
    userChoice = input("Choose an option: ")
    print("")
    if userChoice == "1":
        print("What course would you like to learn more about? Please enter the course code (e.g. CS 106B, MATH 51, BIO 83 etc.)")
        courseChoice = input("Enter course: ")
        classData = retrieveClass(StanfordClassList, className = courseChoice)
        if classData is None:
            classData = retrieveClass(StanfordClassList, classTitle = courseChoice)
        if classData is None:
            print("Oops!! That course isn't offered at Stanford")
        else:
            print("")
            print("")
            classData.printOutCourse()
    elif userChoice == "2":
        userClasses = []
        print("Let's help you out! Enter all the courses you have completed so far. When you are done entering courses, type \"DONE\" or press enter")
        print("Please enter the course code (e.g. CS 106B, MATH 51, BIO 83 etc.)")
        courseChoice = input("Enter a course: ")
        while (courseChoice.upper() != "DONE" and courseChoice != ""):
            userClasses.append(courseChoice.upper())
            courseChoice = input("Enter a course: ")
        allPossibleClasses = determineFutureClasses(userClasses, StanfordClassList)
        print("")
        print("Here are the classes that you have acquired the prerequisites for! (note: this doesn't include courses with no prereqs)")
        print("-------------------------------------------------------------------------------------------------------------------------")
        for possibleClass in allPossibleClasses:
            print(possibleClass.name + ": " + possibleClass.title)
    elif userChoice == "3":
        print("For what course would you like to know ALL the classes you must take prior to it? Please enter the course code (e.g. CS 106B, MATH 51, BIO 83 etc.)")
        courseChoice = input("Enter course: ")
        classToDetermine = retrieveClass(StanfordClassList, className = courseChoice)
        if classToDetermine is None:
            classToDetermine = retrieveClass(StanfordClassList, classTitle = courseChoice)
        if classToDetermine is None:
            print("Oops!! That course isn't offered at Stanford")
        else:
            print("")
            print("")
            allPreReqs = determineAllRequiredPrerequisites(classToDetermine)
            print("")
            print("Here are all the classes you must take before you may take " + classToDetermine.name)
            print("Warning: some courses may be equivalent courses, and only one needs to be taken")
            print("-------------------------------------------------------------------------------------------------------------------------")
            for requiredClass in allPreReqs:
                print(requiredClass.name + ": " + requiredClass.title)
    elif userChoice == "4":
        for course in StanfordClassList:
            print("")
            print("----------------------------------------------------------------")
            course.printOutCourse()
    elif userChoice == "5":
        nonreqs = determineAllNonPrerequisiteCourses(StanfordClassList)
        for possibleClass in nonreqs:
            print(possibleClass.name + ": " + possibleClass.title)
        print("")
        print("")
        print("Above is a list of all courses that have no prerequisites!")
    elif userChoice == "6":
        break
    else:
        print("Sorry, that's not an option :/")
    print("  ")
    print("")
