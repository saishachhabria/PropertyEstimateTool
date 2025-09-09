"""
Simple pytest configuration for estimate app tests
"""
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'property_tool.settings')
django.setup()

import pytest
from decimal import Decimal
from django.test import Client
from estimate.models import PropertyInquiry, PropertyEstimate


@pytest.fixture
def client():
    """Provide a Django test client"""
    return Client()


@pytest.fixture
def sample_inquiry():
    """Create a basic property inquiry"""
    return PropertyInquiry.objects.create(
        address="Test Farm, Test State",
        lot_size=Decimal("25.0"),
        user_context="Test context"
    )


@pytest.fixture
def completed_inquiry():
    """Create a completed inquiry with questionnaire responses"""
    inquiry = PropertyInquiry.objects.create(
        address="Completed Test Farm",
        lot_size=Decimal("30.0"),
        user_context="Test with questionnaire",
        questionnaire_completed=True,
        current_question=4,
        questionnaire_responses={
            "1": "I want to improve profitability and soil health",
            "2": "Currently have pasture and some crops",
            "3": "Can invest $50,000 and hire help",
            "4": "Excited about carbon credits and sustainability"
        }
    )
    return inquiry


@pytest.fixture
def sample_estimate(completed_inquiry):
    """Create a complete estimate with financial data"""
    return PropertyEstimate.objects.create(
        inquiry=completed_inquiry,
        project_name="Test Regenerative Project",
        project_description="A comprehensive test project description.",
        location="Test Farm, USA",
        area_hectares=Decimal("12.14"),
        total_revenue_10_year=Decimal("500000.00"),
        total_costs_10_year=Decimal("350000.00"),
        total_net_cash_flow_10_year=Decimal("150000.00"),
        yearly_financials=[
            {
                "year": i,
                "total_revenue": str(40000 + i * 5000),
                "total_costs": str(35000 + i * 1000),
                "net_cash_flow": str(5000 + i * 4000),
                "agricultural_sales": str(30000 + i * 4000),
                "ecosystem_services": str(5000 + i * 500),
                "subsidies_incentives": str(5000 + i * 500)
            }
            for i in range(1, 11)
        ],
        status='completed',
        ai_model_used='mock-ai-v1'
    )