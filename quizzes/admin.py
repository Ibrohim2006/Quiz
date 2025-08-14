from django.contrib import admin
from .models import Subject, Question, Answer, UserQuiz



admin.site.register(Subject)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(UserQuiz)
