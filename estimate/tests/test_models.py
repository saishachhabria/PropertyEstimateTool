import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from estimate.models import PropertyInquiry, PropertyEstimate, get_question


@pytest.mark.django_db
class TestPropertyInquiry:
    """Test PropertyInquiry model"""
    
    def test_create_property_inquiry(self):
        """Test creating a property inquiry"""
        inquiry = PropertyInquiry.objects.create(
            address="123 Test Street, Test City",
            lot_size=Decimal("10.5"),
            user_context="Test farm"
        )
        
        assert inquiry.id is not None
        assert inquiry.address == "123 Test Street, Test City"
        assert inquiry.lot_size == Decimal("10.5")
        assert inquiry.current_question == 1
        assert inquiry.questionnaire_completed is False
        
    def test_questionnaire_progress(self):
        """Test questionnaire progress calculation"""
        
        inquiry = PropertyInquiry.objects.create(
            address="Test Farm",
            lot_size=Decimal("5.0")
        )
        
        assert inquiry.get_progress_percentage() == 25
        
        inquiry.current_question = 2
        inquiry.save()
        assert inquiry.get_progress_percentage() == 50
        
        inquiry.current_question = 4
        inquiry.questionnaire_completed = True
        inquiry.save()
        assert inquiry.get_progress_percentage() == 100


@pytest.mark.django_db
class TestPropertyEstimate:
    """Test PropertyEstimate model"""
    
    def test_create_estimate(self):
        """Test creating a property estimate"""
        inquiry = PropertyInquiry.objects.create(
            address="Test Farm",
            lot_size=Decimal("15.0")
        )
        
        estimate = PropertyEstimate.objects.create(
            inquiry=inquiry,
            project_name="Test Project",
            total_revenue_10_year=Decimal("500000"),
            total_costs_10_year=Decimal("350000"),
            total_net_cash_flow_10_year=Decimal("150000"),
            status="completed"
        )
        
        assert estimate.inquiry == inquiry
        # ROI = (150000 / 350000) * 100 = 42.86%
        assert abs(estimate.roi_percentage - 42.86) < 0.1
    
    def test_get_chart_data(self):
        """Test chart data formatting"""
        inquiry = PropertyInquiry.objects.create(
            address="Chart Test",
            lot_size=Decimal("5.0")
        )
        
        yearly_data = [
            {
                "year": 1,
                "total_revenue": "50000",
                "total_costs": "40000",
                "net_cash_flow": "10000",
                "agricultural_sales": "45000",
                "ecosystem_services": "0",
                "subsidies_incentives": "5000"
            }
        ]
        
        estimate = PropertyEstimate.objects.create(
            inquiry=inquiry,
            yearly_financials=yearly_data
        )
        
        chart_data = estimate.get_chart_data()
        assert len(chart_data) == 1
        assert chart_data[0]["year"] == 1
        assert chart_data[0]["net_cash_flow"] == 10000.0


class TestQuestionnaireQuestions:
    """Test questionnaire questions"""
    
    def test_get_valid_questions(self):
        """Test getting valid questions"""
        question_1 = get_question(1)
        assert question_1 is not None
        assert "goal" in question_1["title"].lower()
        assert question_1["required"] is True
        
    def test_get_invalid_questions(self):
        """Test invalid question numbers"""
        assert get_question(0) is None
        assert get_question(5) is None