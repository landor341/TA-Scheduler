from dataclasses import dataclass
from datetime import time
from typing import List

from ta_scheduler.models import Semester, Course, User


@dataclass
class UserRef:
    """
    A dataclass that exposes only enough information to display a users name and link to their profile
    """
    name: str
    username: str

@dataclass
class LabSectionRef:
    """
    A dataclass that exposes only enough information to display a lab sections number and
    instructor (if an instructor exists)
    """
    section_number: str
    instructor: UserRef | None

@dataclass
class CourseSectionRef:
    """
    A dataclass that exposes only enough information to display a course section's number and
    instructor (if an instructor exists).
    """
    section_number: str
    instructor: UserRef


@dataclass
class CourseFormData:
    """
    A dataclass that exposes the data necessary to fill/submit the CourseForm
    """
    course_code: str
    course_name: str
    semester: str
    ta_username_list: str

@dataclass
class CourseRef:
    """
    A dataclass that exposes only enough information to expose a course code and name
    """
    course_code: str
    course_name: str

@dataclass
class TACourseRef(CourseRef):
    """
    A dataclass that exposes a TAs connection to a course, including basic course info, the course instructor,
    the users TA status and the lab sections assigned to the user
    """
    instructor: UserRef | None
    is_grader: bool
    assigned_lab_sections: List[int]

@dataclass
class CourseOverview:
    code: str
    name: str
    semester: str | None
    ta_list: List[UserRef]
    course_sections: List[CourseSectionRef]
    lab_sections: List[LabSectionRef]

@dataclass
class UserProfile:
    """
    A dataclass that exposes all public information related to a user
    """
    name: str
    email: str
    role: str
    office_hours: str | None
    courses_assigned: List[CourseOverview]
    skills: List[str] | None

@dataclass
class PrivateUserProfile(UserProfile):
    """
    A dataclass that exposes all user information, private and public
    """
    address: str
    phone: str


@dataclass
class UserFormData:
    """
    A dataclass that contains all the information used to fill the user creation/editing form
    """
    username: str | None
    first_name: str | None
    last_name: str | None
    role: str | None
    office_hours: str | None
    email: str | None
    address: str | None
    phone: str | None
    skills: str or []


@dataclass
class SectionFormData:
    """
    A dataclass that exposes the data necessary to fill/submit section creation
    """
    course: CourseRef
    section_number: int
    days: str | None
    start_time: time | None
    end_time: time | None
    section_type: str | None


@dataclass
class LabSectionFormData(SectionFormData):
    """
    A dataclass that exposes the data necessary to fill/submit the LabCreationForm
    """
    section_type = "Lab"

@dataclass
class CourseSectionFormData(SectionFormData):
    """
    A dataclass that exposes the data necessary to fill/submit the CourseSectionCreationForm
    """
    instructor: UserRef
    section_type = "Course"
