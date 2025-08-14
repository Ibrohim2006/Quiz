from django.urls import path
from .views import QuestionViewSet, SubjectViewSet, AnswerSubmitViewSet, EmailViewSet

urlpatterns = [
    path('subjects/', SubjectViewSet.as_view({'get': 'list'})),
    path('subjects/questions/', QuestionViewSet.as_view({'post': 'create'})),
    path('questions/answers/start/', AnswerSubmitViewSet.as_view({'post': 'start'})),
    path('questions/answers/', AnswerSubmitViewSet.as_view({'post': 'post'})),
    path('emails/', EmailViewSet.as_view({'post': 'post'}))
]
