
from os import name
from django.urls import path
from . import views
urlpatterns = [
    path('',views.TeamCreateView.as_view(), name='home'),
    path('upload/',views.file_upload_view, name='upload')
]