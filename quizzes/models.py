from django.db import models
from authentication.models import UserModel, BaseModel
from django.utils import timezone

ANSWER_CHOICES = (
    ('A', 'A'),
    ('B', 'B'),
    ('C', 'C'),
    ('D', 'D'),
)


class Subject(BaseModel):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Question(BaseModel):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    options = models.JSONField(default=dict)
    correct_answer = models.CharField(max_length=1, choices=ANSWER_CHOICES)
    image = models.ImageField(upload_to='questions/', null=True, blank=True)

    def __str__(self):
        return self.text


class UserQuiz(BaseModel):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='quizzes')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='user_quizzes')
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    score = models.PositiveIntegerField(default=0)
    questions = models.JSONField(default=list)
    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.subject}"


class Answer(BaseModel):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    selected_answer = models.CharField(max_length=1, choices=ANSWER_CHOICES)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.question} - {self.selected_answer}"
