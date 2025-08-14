from django.db import models
from authentication.models import UserModel
from datetime import datetime

ANSWER_CHOICE = (
    (1, 'A'),
    (2, 'B'),
    (3, 'C'),
    (4, 'D'),
)


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Subject(BaseModel):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Question(BaseModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    question = models.TextField()
    option_a = models.TextField()
    option_b = models.TextField()
    option_c = models.TextField()
    option_d = models.TextField()
    correct_answer = models.IntegerField(choices=ANSWER_CHOICE)
    question_image = models.ImageField(upload_to='images/', null=True, blank=True)


class UserQuiz(BaseModel):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    start_time = models.DateTimeField(default=datetime.now)
    end_time = models.DateTimeField(default=datetime.now)
    attempts = models.PositiveIntegerField(default=0)
    score = models.PositiveIntegerField(default=0)
    questions = models.JSONField(default=list)

    completed = models.BooleanField(default=False)


class Answer(BaseModel):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='user')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answer')
    selected_answer = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.selected_answer
