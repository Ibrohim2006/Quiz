from django.urls import path
from .views import QuestionViewSet, SubjectViewSet, AnswerViewSet, EmailViewSet

urlpatterns = [
    path('subjects/', SubjectViewSet.as_view({'get': 'list'})),

    path('subjects/questions/', QuestionViewSet.as_view({'post': 'post'})),

    path('questions/answers/start/', AnswerViewSet.as_view({'post': 'start'})),

    path('questions/answers/', AnswerViewSet.as_view({'post': 'post'})),

    path('emails/', EmailViewSet.as_view({'post': 'post'})),
]
