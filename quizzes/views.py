from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import QuestionSerializer, SubjectSerializer, UserQuizSerializer
from rest_framework.permissions import IsAuthenticated
import random
from .utils import send_message_telegram
from django.utils import timezone
from django.conf import settings
from django.core.mail import EmailMessage
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class EmailViewSet(ViewSet):
    @swagger_auto_schema(
        operation_description="Send email with quiz results",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email address to send to'),
                'session_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Session ID'),
            }
        ),
        responses={200: 'Email sent!'},
        tags=['Quiz']
    )
    def post(self, request):
        user = request.user
        email = request.data['email']
        session_id = request.data.get('session_id')
        ses = UserQuiz.objects.filter(id=session_id, user=user).first()
        session_serializer = UserQuizSerializer(ses)
        d = session_serializer.data
        email_message = EmailMessage(
            'Test email Subject',
            F'Test email body, This message is from python {d.get("user"), d.get("subject"), d.get("score"), d.get("attempts"), d.get("start_time"), d.get("end_time")}',
            settings.EMAIL_HOST_USER,
            [email]
        )
        email_message.send(fail_silently=False)
        return Response(
            data={'message': 'Email sent!'},
            status=status.HTTP_200_OK
        )


class SubjectViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all subjects",
        responses={200: SubjectSerializer(many=True)},
        tags=['Quiz']
    )
    def list(self, request):
        serializer = SubjectSerializer(Subject.objects.all(), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class QuestionViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get random questions for a subject via POST",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['name', 'session_id'],
            properties={
                'name': openapi.Schema(type=openapi.TYPE_STRING, description='Subject name'),
                'session_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='UserQuiz session ID'),
            },
        ),
        responses={200: QuestionSerializer(many=True)},
        tags=["Quiz"]
    )
    def create(self, request):
        # POST data
        subject_name = request.data.get('name')
        session_id = request.data.get('session_id')

        if not subject_name:
            return Response({'error': 'Subject field is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not session_id:
            return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Subjectni olish
        subject = Subject.objects.filter(name=subject_name).first()
        if not subject:
            return Response({'error': 'Subject does not exist'}, status=status.HTTP_404_NOT_FOUND)

        # Sessiyani olish
        session = UserQuiz.objects.filter(id=session_id, user=request.user).first()
        if not session:
            return Response({'error': 'Session does not exist'}, status=status.HTTP_404_NOT_FOUND)

        # Tasodifiy 10 savol tanlash
        questions = list(Question.objects.filter(subject=subject))
        random.shuffle(questions)
        questions = questions[:10]

        # Sessiyaga saqlash
        session.questions = [q.id for q in questions]
        session.save(update_fields=['questions'])

        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AnswerSubmitViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Start a quiz session",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
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
        user = request.user
        subject_name = request.data.get('subject_name')

        if not subject_name:
            return Response(
                data={'error': 'Subject field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subject = Subject.objects.filter(name=subject_name).first()
        if not subject:
            return Response(
                data={'error': 'Subject not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        session = UserQuiz.objects.create(user=user, subject=subject)
        return Response(
            data={'message': 'Quiz started successfully', 'session_id': session.id},
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(
        operation_description="Submit an answer to a quiz question",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'question_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Question ID'),
                'answer': openapi.Schema(type=openapi.TYPE_STRING, description='Answer choice'),
                'session_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='Session ID'),
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
        user = request.user
        question_id = int(request.data.get('question_id'))
        answer = request.data.get('answer')
        session_id = request.data.get('session_id')
        session = UserQuiz.objects.filter(id=session_id, user=user).first()
        answer = Answer.objects.all()
        if not session:
            return Response(
                data={"error": "Session does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
        if question_id not in session.questions:
            return Response(
                data={"error": "Invalid question for this session"},
                status=status.HTTP_400_BAD_REQUEST
            )
        question = Question.objects.filter(id=question_id).first()
        if not question:
            return Response(
                data={"error": "Question does not exist"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if session.attempts >= 10:
            session.is_completed = True
            session.end_time = timezone.now()
            session.save()
            answer.delete()
            return Response(
                data={"Message": "You finished test"},
                status=status.HTTP_200_OK
            )

        time_limit = session.start_time + timezone.timedelta(minutes=3)
        if timezone.now() > time_limit:
            session.score = 0
            session.completed = True
            session.end_time = timezone.now()
            session.save()
            answer.delete()
            return Response(
                data={'message': 'Time limit ended'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if session.completed:
            return Response(
                data={'message': 'Quiz already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if answer not in ['A', 'B', 'C', 'D']:
            return Response({"error": "'A', 'B', 'C', or 'D' answers only"},
                            status=status.HTTP_400_BAD_REQUEST)

        answer_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
        user_answer_value = answer_map[answer]
        is_correct = user_answer_value == question.correct_answer

        if Answer.objects.filter(user=user, question=question).exists():
            return Response({"error": "You have already answered this question"},
                            status=status.HTTP_400_BAD_REQUEST)

        Answer.objects.create(
            user=user,
            question=question,
            selected_answer=answer,
            is_correct=is_correct
        )

        if is_correct:
            session.score += 1
        session.attempts += 1

        session.save()

        ses = UserQuiz.objects.filter(id=session_id, user=user).first()
        session_serializer = UserQuizSerializer(ses)
        d = session_serializer.data
        send_message_telegram(d)
        return Response({'is_correct': is_correct})
