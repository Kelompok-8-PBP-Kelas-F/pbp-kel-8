from django.urls import path

from outfitbuilder import views

app_name = "outfitbuilder"

urlpatterns = [
    path("outfitbuilder/", views.ob_page, name="ob_page"),
]