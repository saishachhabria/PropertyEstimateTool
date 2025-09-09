import pytest
import json
from django.urls import reverse
from django.test import Client
from decimal import Decimal
from estimate.models import PropertyInquiry, PropertyEstimate


@pytest.mark.django_db
class TestPropertyEstimateView:
    """Test the main form view"""
    
    def test_get_form_page(self, client):
        """Test accessing the form page"""
        response = client.get(reverse('estimate:property_estimate'))
        assert response.status_code == 200
        assert 'form' in response.context
    
    def test_submit_valid_form(self, client):
        """Test submitting valid form"""
        form_data = {
            'address': '123 Test Farm Road',
            'lot_size': '10.5',
            'unit': 'acres',
            'user_context': 'Test context'
        }
        
        response = client.post(
            reverse('estimate:property_estimate'),
            data=form_data,
            follow=True
        )
        
        assert response.status_code == 200
        
        # Check inquiry was created
        inquiry = PropertyInquiry.objects.first()
        assert inquiry is not None
        assert inquiry.address == '123 Test Farm Road'
        assert inquiry.lot_size == Decimal('10.5')


@pytest.mark.django_db
class TestQuestionnaireView:
    """Test questionnaire flow"""
    
    @pytest.fixture
    def inquiry(self):
        return PropertyInquiry.objects.create(
            address='Test Farm',
            lot_size=Decimal('10.0')
        )
    
    def test_get_questionnaire_page(self, client, inquiry):
        """Test accessing questionnaire"""
        url = reverse('estimate:questionnaire', kwargs={
            'inquiry_id': inquiry.id,
            'question': 1
        })
        response = client.get(url)
        
        assert response.status_code == 200
        assert 'question_number' in response.context
        assert response.context['question_number'] == 1
    
    def test_submit_response(self, client, inquiry):
        """Test submitting questionnaire response"""
        url = reverse('estimate:questionnaire', kwargs={
            'inquiry_id': inquiry.id,
            'question': 1
        })
        
        response = client.post(url, {
            'response': 'I want to improve soil health'
        }, follow=True)
        
        assert response.status_code == 200
        
        # Check response was saved
        inquiry.refresh_from_db()
        assert '1' in inquiry.questionnaire_responses


@pytest.mark.django_db
class TestResultsView:
    """Test results page"""
    
    def test_view_results(self, client, sample_estimate):
        """Test viewing results"""
        url = reverse('estimate:results', kwargs={
            'inquiry_id': sample_estimate.inquiry.id
        })
        
        response = client.get(url)
        assert response.status_code == 200
        assert 'estimate' in response.context
        assert sample_estimate.project_name in response.content.decode()