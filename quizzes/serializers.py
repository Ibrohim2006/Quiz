from rest_framework import serializers
from .models import Subject, Question, UserQuiz, Answer


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'subject', 'text', 'options', 'correct_answer', 'image']


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'user', 'question', 'selected_answer', 'is_correct']
        read_only_fields = ['is_correct']


class UserQuizSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    subject_detail = SubjectSerializer(source='subject', read_only=True)

    class Meta:
        model = UserQuiz
        fields = [
            'id',
            'user',
            'subject',
            'subject_detail',
            'start_time',
            'end_time',
            'attempts',
            'score',
            'questions',
            'completed',
            'answers'
        ]
