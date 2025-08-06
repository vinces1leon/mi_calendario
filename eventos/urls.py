from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendario, name='calendario'),
    path('eventos_json/', views.eventos_json, name='eventos_json'),
    path('agregar_persona/', views.agregar_persona, name='agregar_persona'),
    path('eliminar_persona/', views.eliminar_persona, name='eliminar_persona'),
    path('registrar_actividad/', views.registrar_actividad, name='registrar_actividad'),
    path('resumen/<str:fecha>/', views.resumen_registros, name='resumen_por_fecha'),
    path('deshacer_ultimo_registro/', views.deshacer_ultimo_registro, name='deshacer_ultimo_registro'),
    path('calendario/', views.calendario, name='calendario'),
    path('resumen/exportar/<str:fecha>/', views.exportar_resumen_excel, name='exportar_excel'),

]
