from django.urls import path

from outfitbuilder.views import ob_page

app_name = "outfitbuilder"

urlpatterns = [
    path("outfitbuilder/", ob_page, name="ob_page"),
]