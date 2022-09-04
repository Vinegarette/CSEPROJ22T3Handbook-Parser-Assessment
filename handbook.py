"""
Inside conditions.json, you will see a subset of UNSW courses mapped to their
corresponding text conditions. We have slightly modified the text conditions
to make them simpler compared to their original versions.

Your task is to complete the is_unlocked function which helps students determine
if their course can be taken or not.

We will run our hidden tests on your submission and look at your success rate.
We will only test for courses inside conditions.json. We will also look over the
code by eye.

NOTE: We do not expect you to come up with a perfect solution. We are more interested
in how you would approach a problem like this.
"""
import json
import re
import string


'''
Solution idea was to take a Composite Design Pattern and apply it to the problem.
The biggest issue with this solution was dealing with String parsing and creation of the actual "tree" structure.
Majority of cases are dealt with through different Python classes, with a shared Evaluate function.

Issues include:
1. Lack of support for bracketed conditions; Limitation of the String parsing and using translate to remove all punctuation. With more time, this could be resolved :(
2. Regex to determine type of class to use means that in cases of different formatting, or spelling errors, there will be errors.
'''


class AND:

    def add_left(self, left):
        self.left = left

    def add_right(self, right):
        self.right = right

    def evaluate(self, courses_list):

        return self.left.evaluate(courses_list) and self.right.evaluate(courses_list)
        # Evaluate left and right conditions


class OR:

    def add_left(self, left):
        self.left = left

    def add_right(self, right):
        self.right = right

    def evaluate(self, courses_list):
        return self.left.evaluate(courses_list) or self.right.evaluate(courses_list)
        # Evaluate left and right conditions


class GROUP:
    def __init__(self, courses, target):
        self.courses = courses
        self.target = target/6

    def evaluate(self, courses_list):
        valid = [c for c in self.courses if c in courses_list]
        return len(valid) >= self.target


'''
Single value case; Evaluate if the course is in the courses_list
'''


class VALUE:
    def __init__(self, value):
        self.value = value

    def evaluate(self, courses_list):

        for course in courses_list:
            course = re.search("[0-9]{4}", course).group()
            if course == self.value:
                return True

        return False


'''
Completion of XX units case.
'''


class COMPLETION:
    def __init__(self, target):
        self.target = target/6

    def evaluate(self, courses_list):
        return len(courses_list) >= self.target


'''
Multiple Units in a certain COMP level case.
'''


class LEVELS:
    def __init__(self, level, target):
        self.level = level
        self.target = target/6

    def evaluate(self, courses_list):
        count = 0
        pattern = f"^{self.level}"
        for course in courses_list:
            if re.match(pattern, course):
                count += 1

        return count >= self.target


# NOTE: DO NOT EDIT conditions.json
with open("./conditions.json") as f:
    CONDITIONS = json.load(f)
    f.close()


'''
Given a prerequisite string, clean and return a list of appropriate course requirements
Cleaning results in issues with brackets and proper ordering.
'''


def clean(prereq):

    # Clearing Prerequisite conditions with ":"
    index = prereq.find(':')
    prereq = prereq[index + 1:]

    # This removes brackets; Invalidates certain cases with brackets.
    prereq = prereq.translate(str.maketrans(
        '', '', string.punctuation))
    # Evaluate within brackets first.
    prereq = " ".join(prereq.split())
    prereq = prereq.upper()
    return prereq


'''
1. Given the current target_course, check if current prereqs are passable. Return True if so.
2. Else, we go through the prereqs of the current course, recursing. If at any time it is false,
we return False.
'''


'''
Create a Compound Node (AND or OR node)
Given a list of prereqs, also include adjacent conditions in the Compound Node object.
This can be another Compound Node or Leaf Node
'''


def create_compound(arg, prereq_list, i, special_list):

    left = prereq_list[i-1]
    right = prereq_list[i+1]
    if (arg == "AND"):
        node = AND()
    elif arg == "OR":
        node = OR()

    if (isinstance(left, str)):

        if re.search("SPECIAL[0-9]+", left):
            node.add_left(special_list[int(left[7:])])
        else:
            # Extract Course Code
            code = re.search("[0-9]{4}", left).group()
            node.add_left(VALUE(code))
    else:
        node.add_left(left)

    if (isinstance(right, str)):
        if re.search("SPECIAL[0-9]+", right):
            node.add_left(special_list[int(right[7:])])
        else:
            code = re.search("[0-9]{4}", right).group()
            node.add_right(VALUE(code))
    else:
        node.add_right(right)

    return node


def is_unlocked(courses_list, target_course):
    """Given a list of course codes a student has taken, return true if the target_course
    can be unlocked by them.

    You do not have to do any error checking on the inputs and can assume that
    the target_course always exists inside conditions.json

    You can assume all courses are worth 6 units of credit
    """

    # TODO: COMPLETE THIS FUNCTION!!!

    '''
    The solution is a composite pattern solution, with AND/OR nodes as Compound Nodes and
    Courses as the Leaf Nodes.
    
    '''

    # Find Target Course's Courses List
    with open("./conditions.json") as f:
        CONDITIONS = json.load(f)
        # Generate conditions properly
        # Generate the target_courses' requirements
        prereq = clean(CONDITIONS[target_course])

        # List of Nodes that must be evaluated.
        values = []

        # Identify the Special Cases, where it is not OR/AND/Simple Course
        special = re.findall("[0-9]+ UNITS OF CREDIT IN .*",
                             prereq) + re.findall("COMPLETION OF [0-9]{2} UNITS OF CREDIT", prereq)

        # Specials are given unique Special Ids, to allow for AND/OR interactions.
        special_list = []
        for i, s in enumerate(special):

            # Determine if it is a :
            # 1. LEVELS (XX units of credit in level X courses)
            # 2. GROUP (XX units of credit in (course, course))
            # 3. COMPLETION (XX units completed)
            if re.search("IN LEVEL [0-9] COMP COURSES", s):
                prereq = prereq.replace(s, "SPECIAL" + str(i))
                s = s.split()
                node = LEVELS(int(s[6]), int(s[0]))
                values.append(node)
            elif re.search("[0-9]{4}", s):
                prereq = prereq.replace(s, "")
                s = s.split()
                node = GROUP(s[5:], int(s[0]))
                values.append(node)
            elif re.search("COMPLETION OF", s):
                prereq = prereq.replace(s, "")
                s = s.split()
                node = COMPLETION(int(s[2]))
                values.append(node)

            special_list.append(node)

        # Generate a list of conditions for the prereq.
        prereq_list = [p for p in prereq.split() if p != ""]

        # First, generate all existing AND/OR nodes.
        # Remove adjacent conditions.
        i = 0
        length = len(prereq_list)
        while i < length:
            arg = prereq_list[i]
            if arg == "AND" or arg == "OR":
                compound = create_compound(arg, prereq_list, i, special_list)
                values.append(compound)
                prereq_list = prereq_list[0:i-1] + \
                    [compound] + prereq_list[i+2:]
            else:
                i += 1
            length = len(prereq_list)

        # Second, generate all remaining simple Value nodes.
        for v in prereq_list:
            if isinstance(v, str):
                code = re.search("[0-9]{4}", v).group()
                values.append(VALUE(code))

        # Evaluate all nodes for errors.
        for v in values:
            if v.evaluate(courses_list) == False:
                return False

    return True
