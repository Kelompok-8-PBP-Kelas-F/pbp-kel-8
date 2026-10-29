from django.urls import path

from . import views

app_name = "event"

urlpatterns = [
    path("event/", views.event_page, name="event_page"),
]
