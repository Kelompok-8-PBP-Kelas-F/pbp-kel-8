from django.urls import path

from . import views

app_name = "event"

urlpatterns = [
    path("event/", views.event_page, name="event_page"),
    path("event/create/", views.event_create, name="event_create"),
    path("event/<uuid:event_id>/", views.event_detail, name="event_detail"),
    path(
        "event/<uuid:event_id>/edit/",
        views.event_edit,
        name="event_edit",
    ),
    path(
        "event/<uuid:event_id>/delete/",
        views.event_delete,
        name="event_delete",
    ),
    path(
        "event/<uuid:event_id>/register/",
        views.register_for_event,
        name="register_for_event",
    ),
]
