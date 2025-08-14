from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage
import random
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Subject, Question, UserQuiz, Answer
from .serializers import QuestionSerializer, SubjectSerializer, UserQuizSerializer
from .utils import send_message_telegram


class EmailViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Send email with quiz results",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'session_id'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address to send to'),
                'session_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='UserQuiz session ID'),
            }
        ),
        responses={200: 'Email sent!'},
        tags=['Quiz']
    )
    def post(self, request):
        user = request.user
        email = request.data['email']
        session_id = request.data['session_id']

        session = UserQuiz.objects.filter(id=session_id, user=user).first()
        if not session:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        session_serializer = UserQuizSerializer(session)
        data = session_serializer.data

        email_message = EmailMessage(
            'Quiz Results',
            f"User: {data.get('user')}\nSubject: {data.get('subject')}\nScore: {data.get('score')}\n"
            f"Attempts: {data.get('attempts')}\nStart: {data.get('start_time')}\nEnd: {data.get('end_time')}",
            settings.EMAIL_HOST_USER,
            [email]
        )
        email_message.send(fail_silently=False)
        return Response({'message': 'Email sent!'}, status=status.HTTP_200_OK)


class SubjectViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all subjects",
        responses={200: SubjectSerializer(many=True)},
        tags=['Quiz']
    )
    def list(self, request):
        subjects = Subject.objects.all()
        serializer = SubjectSerializer(subjects, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class QuestionViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get 10 random questions for a subject using session",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['subject_name', 'session_id'],
            properties={
                'subject_name': openapi.Schema(type=openapi.TYPE_STRING, description='Subject name'),
                'session_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='UserQuiz session ID'),
            }
        ),
        responses={200: QuestionSerializer(many=True)},
        tags=["Quiz"]
    )
    def post(self, request):
        subject_name = request.data.get('subject_name')
        session_id = request.data.get('session_id')

        if not subject_name or not session_id:
            return Response({'error': 'Subject name and session_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        subject = Subject.objects.filter(name=subject_name).first()
        if not subject:
            return Response({'error': 'Subject not found'}, status=status.HTTP_404_NOT_FOUND)

        session = UserQuiz.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return Response({'error': 'Session does not exist'}, status=status.HTTP_404_NOT_FOUND)

        questions = list(Question.objects.filter(subject=subject))
        random.shuffle(questions)
        questions = questions[:10]

        session.questions = [q.id for q in questions]
        session.save(update_fields=['questions'])

        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AnswerViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Start a new quiz session for a subject",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['subject_name'],
            properties={
                'subject_name': openapi.Schema(type=openapi.TYPE_STRING, description='Subject name'),
            }
        ),
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'message': openapi.Schema(type=openapi.TYPE_STRING),
                'session_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            }
        )},
        tags=['Quiz']
    )
    def start(self, request):
        subject_name = request.data.get('subject_name')
        if not subject_name:
            return Response({'error': 'Subject name is required'}, status=status.HTTP_400_BAD_REQUEST)

        subject = Subject.objects.filter(name=subject_name).first()
        if not subject:
            return Response({'error': 'Subject not found'}, status=status.HTTP_404_NOT_FOUND)

        session = UserQuiz.objects.create(user=request.user, subject=subject)
        return Response({'message': 'Quiz started', 'session_id': session.id}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Submit an answer for a question",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['session_id', 'question_id', 'answer'],
            properties={
                'session_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='UserQuiz session ID'),
                'question_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Question ID'),
                'answer': openapi.Schema(type=openapi.TYPE_STRING, description='Answer choice: A/B/C/D'),
            }
        ),
        responses={200: openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'is_correct': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            }
        )},
        tags=['Quiz']
    )
    def post(self, request):
        session_id = request.data.get('session_id')
        question_id = request.data.get('question_id')
        answer_choice = request.data.get('answer')

        session = UserQuiz.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return Response({'error': 'Session not found'}, status=status.HTTP_404_NOT_FOUND)

        if question_id not in session.questions:
            return Response({'error': 'Invalid question for this session'}, status=status.HTTP_400_BAD_REQUEST)

        question = Question.objects.filter(id=question_id).first()
        if not question:
            return Response({'error': 'Question not found'}, status=status.HTTP_404_NOT_FOUND)

        if answer_choice not in ['A', 'B', 'C', 'D']:
            return Response({'error': 'Answer must be A, B, C, or D'}, status=status.HTTP_400_BAD_REQUEST)

        is_correct = answer_choice == question.correct_answer

        if Answer.objects.filter(user=request.user, question=question).exists():
            return Response({'error': 'You already answered this question'}, status=status.HTTP_400_BAD_REQUEST)

        Answer.objects.create(user=request.user, question=question, selected_answer=answer_choice, is_correct=is_correct)

        session.attempts += 1
        if is_correct:
            session.score += 1
        session.save(update_fields=['score', 'attempts'])

        send_message_telegram(UserQuizSerializer(session).data)
        return Response({'is_correct': is_correct}, status=status.HTTP_200_OK)
