from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_pdf, name='upload_pdf'),
    path('result/<int:pk>/', views.result_view, name='result'),
    path('api/pdf-extract/', views.pdf_extraction_api, name='pdf_extraction_api'),
]
