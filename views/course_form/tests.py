from django.test import TestCase


# Test getting course form for new course (only admin can get)
# Test getting course form for existing course (only admin can get)
# Test getting course form for fake course (redirect to home)
# Test saving new course form with empty data
# Test saving new course form with malformed data
# Test saving new course form with good data
# Test saving existing course with empty data
# Test saving existing course with malformed data
# Test saving existing course with good data

class TestGetNewCourseForm(TestCase):
    pass


class TestPostCourseForm(TestCase):
    pass # NOTE: Make sure to test that admins cant edit each other
