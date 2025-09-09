import pytest
import asyncio
from decimal import Decimal
from estimate.ai_service import (
    PropertyEstimateRequest,
    PropertyEstimateResponse,
    MockPropertyEstimateAI,
    FallbackPropertyEstimateAI
)


@pytest.mark.asyncio
class TestPropertyEstimateAI:
    """Test AI service"""
    
    async def test_mock_ai_service(self):
        """Test mock AI service works"""
        service = MockPropertyEstimateAI()
        
        request = PropertyEstimateRequest(
            address="Test Farm, Test State",
            lot_size=Decimal("25.0"),
            user_context="Test context"
        )
        
        result, raw_response = await service.generate_estimate(request)
        
        assert isinstance(result, PropertyEstimateResponse)
        assert result.project_name is not None
        assert len(result.yearly_financials) == 10
        assert result.total_revenue_10_year > 0
    
    async def test_fallback_service(self):
        """Test fallback AI service"""
        service = FallbackPropertyEstimateAI()
        
        request = PropertyEstimateRequest(
            address="Test Ranch, Texas",
            lot_size=Decimal("100.0")
        )
        
        result, raw_response = await service.generate_estimate(request)
        
        assert isinstance(result, PropertyEstimateResponse)
        assert result.project_name is not None
        assert 'model_used' in raw_response
    
    async def test_request_validation(self):
        """Test request validation"""
        # Valid request should work
        request = PropertyEstimateRequest(
            address="Valid Farm Address",
            lot_size=Decimal("10.0")
        )
        assert request.address == "Valid Farm Address"
        assert request.lot_size == Decimal("10.0")