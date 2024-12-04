from django.contrib.auth.hashers import make_password
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission


class Semester(models.Model):
    semester_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()

    # convenient format for views
    def __str__(self):
        return f"{self.semester_name}"

    # fetch all courses in semester (useful for searching)
    def get_all_courses(self):
        return self.courses.all()

class Course(models.Model):
    course_code = models.CharField(max_length=255)
    course_name = models.CharField(max_length=255)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name="courses")

    # return all lab sections for the course
    def get_lab_sections(self):
        return self.labsection_set.all()



# extending the Django default User class for User to avoid redefining common functionality
class User(AbstractUser):
    ROLE_CHOICES = [
        ('Instructor', 'Instructor'),
        ('TA', 'TA'),
        ('Admin', 'Admin'),
    ]
    #extra fields to work with our schema on top of default fields
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    office_hours = models.TextField(blank=True, null=True)

    #  Explicitly define related names to avoid clashes
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_set",
        blank=True,
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_set",
        blank=True,
    )

    def save(self, *args, **kwargs):
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    # returns assigned courses based on role (none for admin)
    def get_assigned_courses(self):
        if self.role == "Instructor":
            return self.coursesection_set.values("course")
        elif self.role == "TA":
            return self.tacourseassignment_set("course")
        return Course.objects.none()




class CourseSection(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    instructor = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'Instructor'}, related_name="coursesection_set")
    course_section_number = models.PositiveIntegerField()
    days = models.CharField(max_length=255, blank=True, null=True)
    start_time = models.TimeField()
    end_time = models.TimeField()



class LabSection(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lab_section_number = models.PositiveIntegerField()
    days = models.CharField(max_length=255, blank=True, null=True)
    start_time = models.TimeField()
    end_time = models.TimeField()

    # useful method to associate lab section with the ta - assuming that one ta per lab section
    def get_ta(self):
        assignment = self.talabassignment_set.first()
        return assignment.ta if assignment else None



class TALabAssignment(models.Model):
    lab_section = models.ForeignKey(LabSection, on_delete=models.CASCADE, related_name="talabassignment_set")
    ta = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'TA'}, related_name="lab_assignments")



class TACourseAssignment(models.Model):
    ta = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'TA'})
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    grader_status = models.BooleanField()
