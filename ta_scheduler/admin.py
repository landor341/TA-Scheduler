from django.contrib import admin
from .models import (
    Semester,
    Course,
    CourseSection,
    LabSection,
    TALabAssignment,
    TACourseAssignment,
    User,
)

# Register your models here
admin.site.register(Semester)
admin.site.register(Course)
admin.site.register(CourseSection)
admin.site.register(LabSection)
admin.site.register(TALabAssignment)
admin.site.register(TACourseAssignment)
admin.site.register(User)



