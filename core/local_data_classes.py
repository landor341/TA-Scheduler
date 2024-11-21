from dataclasses import dataclass
from typing import List

from ta_scheduler.models import Semester


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
    course_code: str | None
    course_name: str | None
    instructor: UserRef | None
    semester: Semester | None
    lab_sections_codes: List[int] | None
    course_sections_codes: List[int] | None


@dataclass
class CourseRef:
    """
    A dataclass that exposes only enough information to expose a course code and name
    """
    course_code: int
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
class UserProfile:
    """
    A dataclass that exposes all public information related to a user
    """
    name: str
    email: str
    role: str
    office_hours: str | None
    courses_assigned: List[CourseRef]


@dataclass
class PrivateUserProfile(UserProfile):
    """
    A dataclass that exposes all user information, private and public
    """
    address: str
    phone: str

@dataclass
class CourseOverview:
    code: str
    name: str
    instructor: UserRef
    course_sections: List[CourseSectionRef]
    lab_sections: List[LabSectionRef]

