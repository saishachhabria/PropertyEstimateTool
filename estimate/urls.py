from django.urls import path
from . import views

app_name = 'estimate'

urlpatterns = [
    
    path('', views.PropertyEstimateView.as_view(), name='property_estimate'),
    
    path('questionnaire/<uuid:inquiry_id>/', views.QuestionnaireView.as_view(), name='questionnaire_start'),
    path('questionnaire/<uuid:inquiry_id>/<int:question>/', views.QuestionnaireView.as_view(), name='questionnaire'),
    
    path('processing/<uuid:inquiry_id>/', views.ProcessingView.as_view(), name='processing'),
    path('generate/<uuid:inquiry_id>/', views.GenerateEstimateView.as_view(), name='generate_estimate'),
    path('results/<uuid:inquiry_id>/', views.ResultsView.as_view(), name='results'),
    
    path('health/', views.health_check, name='health_check'),
    path('status/<uuid:inquiry_id>/', views.estimate_status, name='estimate_status'),
]