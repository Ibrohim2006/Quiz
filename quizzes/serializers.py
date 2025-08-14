from rest_framework import serializers

from .models import *


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ('id', 'subject', 'question', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer')
        extra_kwargs = {
            "correct_answer": {"write_only": True}
        }


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name')


class UserQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserQuiz
        fields = ['id', 'user', 'subject', 'start_time', 'end_time', 'attempts', 'score']
