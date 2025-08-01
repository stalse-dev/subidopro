from django.urls import path
from .views import *

urlpatterns = [
    path('', teste, name='teste'),
]