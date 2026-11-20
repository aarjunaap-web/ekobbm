from django.urls import path
from . import views

urlpatterns = [
    path("", views.beranda, name="beranda"),
    path("prediksi/", views.prediksi, name="prediksi"),
    path("grafik/", views.grafik, name="grafik"),
    path("grafik/penjelasan/", views.penjelasan, name="penjelasan"),
]