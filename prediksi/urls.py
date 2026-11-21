from django.urls import path
from . import views

urlpatterns = [
    path("", views.beranda, name="beranda"),
    path("hitung/", views.hitung, name="hitung"),
    path("api/model/", views.api_model, name="api_model"),
    path("api/tahun/", views.api_tahun, name="api_tahun"),
    path("api/varian/", views.api_varian, name="api_varian"),
    path("wawasan/", views.wawasan, name="wawasan"),
    path("wawasan/penjelasan/", views.wawasan_penjelasan, name="wawasan_penjelasan"),
]