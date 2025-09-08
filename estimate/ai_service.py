import time
import json
import random
import asyncio
from typing import Optional, List, Dict
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class PropertyEstimateRequest(BaseModel):
    
    address: str = Field(..., min_length=5, max_length=500, description="Property address or region")
    lot_size: Decimal = Field(..., gt=0, description="Lot size in acres")
    user_context: Optional[str] = Field(default="", description="Additional context")
    
    @validator('address')
    def validate_address(cls, v):
        if not v.strip():
            raise ValueError('Address cannot be empty')
        return v.strip()


class YearlyFinancials(BaseModel):
    
    year: int = Field(..., description="Year number (1-10)")
    total_revenue: Decimal = Field(..., description="Total revenue for this year")
    total_costs: Decimal = Field(..., description="Total costs for this year") 
    net_cash_flow: Decimal = Field(..., description="Net cash flow for this year")
    agricultural_sales: Decimal = Field(..., description="Revenue from agricultural sales")
    ecosystem_services: Decimal = Field(..., description="Revenue from ecosystem services")
    subsidies_incentives: Decimal = Field(..., description="Revenue from subsidies and incentives")


class PropertyEstimateResponse(BaseModel):
    
    project_name: str = Field(..., description="Name of the regenerative agriculture project")
    project_description: str = Field(..., description="Detailed project description")
    location: str = Field(..., description="Formatted location name")
    area_hectares: Decimal = Field(..., description="Area in hectares")
    
    # 10-year financial projections
    yearly_financials: List[YearlyFinancials] = Field(..., description="10 years of financial data")
    
    # Summary totals (calculated from yearly data)
    total_revenue_10_year: Decimal = Field(..., description="Total revenue over 10 years")
    total_costs_10_year: Decimal = Field(..., description="Total costs over 10 years") 
    total_net_cash_flow_10_year: Decimal = Field(..., description="Total net cash flow over 10 years")


class ProductionPropertyEstimateAI:
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY must be set in settings")
        
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = "gpt-4o-mini"
        logger.info("Production OpenAI AI service initialized")
    
    async def generate_estimate(self, request: PropertyEstimateRequest):
        
        start_time = time.time()
        
        try:
            system_prompt = self._get_system_prompt()
            user_prompt = self._create_user_prompt(request)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=3000,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content.strip()
            result_data = self._parse_openai_response(response_text, request)
            processing_time = time.time() - start_time
            
            logger.info(f"OpenAI estimate generated in {processing_time:.2f}s for {request.address}")
            
            raw_response = {
                'project_name': result_data.project_name,
                'project_description': result_data.project_description,
                'location': result_data.location,
                'area_hectares': str(result_data.area_hectares),
                'yearly_financials': [
                    {
                        'year': year.year,
                        'total_revenue': str(year.total_revenue),
                        'total_costs': str(year.total_costs),
                        'net_cash_flow': str(year.net_cash_flow),
                        'agricultural_sales': str(year.agricultural_sales),
                        'ecosystem_services': str(year.ecosystem_services),
                        'subsidies_incentives': str(year.subsidies_incentives)
                    }
                    for year in result_data.yearly_financials
                ],
                'total_revenue_10_year': str(result_data.total_revenue_10_year),
                'total_costs_10_year': str(result_data.total_costs_10_year),
                'total_net_cash_flow_10_year': str(result_data.total_net_cash_flow_10_year),
                'processing_time_seconds': processing_time,
                'model_used': self.model,
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
            
            return result_data, raw_response
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"OpenAI estimation failed: {str(e)}"
            logger.error(f"{error_msg} (processing_time: {processing_time:.2f}s)")
            raise AIEstimationError(error_msg, processing_time)
    
    def _get_system_prompt(self) -> str:
        
        return """You are an expert agricultural economist and regenerative farming consultant. 
        You analyze land properties and create detailed 10-year financial projections for regenerative agriculture projects.
        
        Your task is to generate realistic, conservative estimates that include:
        1. Year-by-year financial projections (10 years)
        2. Three revenue categories: Agricultural Sales, Ecosystem Services, Subsidies & Incentives
        3. Operating costs that improve over time due to efficiency gains
        4. A compelling project name and description
        
        Consider these factors in your projections:
        - Soil restoration takes 2-3 years to show benefits
        - Carbon credits and ecosystem services start generating revenue in years 3-4
        - Agricultural productivity improves as soil health recovers
        - Operating costs decrease over time due to reduced inputs and improved efficiency
        - Subsidies are typically higher in early years
        - Climate, soil type, and local markets affect profitability
        - Regenerative practices: cover crops, rotational grazing, agroforestry, composting
        
        Return ONLY valid JSON with this exact structure:
        {
            "project_name": "string",
            "project_description": "string (200-400 words)",
            "yearly_projections": [
                {
                    "year": 1,
                    "agricultural_sales": number,
                    "ecosystem_services": number,
                    "subsidies_incentives": number,
                    "total_costs": number
                },
                // ... for years 1-10
            ]
        }
        
        All monetary values should be in USD. Be realistic but optimistic about regenerative agriculture benefits."""
    
    def _create_user_prompt(self, request: PropertyEstimateRequest) -> str:
        
        lot_size_acres = float(request.lot_size)
        lot_size_hectares = lot_size_acres * 0.404686
        
        prompt = f"""Create a detailed 10-year financial projection for a regenerative agriculture project:

                    Property Details:
                    - Location: {request.address}
                    - Size: {lot_size_acres} acres ({lot_size_hectares:.1f} hectares)
                    - Project Type: Regenerative Agriculture Transition

                    Context:
                    {request.user_context if request.user_context else "No additional context provided"}

                    Generate realistic projections considering:
                    - Transition period (years 1-3): Lower yields as soil recovers
                    - Maturity period (years 4-7): Improved productivity and new revenue streams
                    - Optimization period (years 8-10): Peak efficiency and diversified income

                    Revenue Categories:
                    1. Agricultural Sales: Crops, livestock, value-added products
                    2. Ecosystem Services: Carbon credits, water quality, biodiversity payments
                    3. Subsidies & Incentives: Government programs, grants, tax benefits

                    Provide conservative estimates that account for regional agriculture economics and regenerative farming best practices.

                    Return valid JSON only.
            """
        
        return prompt
    
    def _parse_openai_response(self, response_text: str, request: PropertyEstimateRequest) -> PropertyEstimateResponse:
        
        try:
            data = json.loads(response_text)
            
            project_name = data.get('project_name', 'Regenerative Agriculture Project')
            project_description = data.get('project_description', 
                'A comprehensive regenerative agriculture project focused on sustainable farming practices.')
            
            location = self._format_location(request.address)
            area_hectares = Decimal(str(round(float(request.lot_size) * 0.404686, 1)))
            
            yearly_financials = []
            yearly_projections = data.get('yearly_projections', [])
            
            for proj in yearly_projections:
                year = proj.get('year', 1)
                agricultural_sales = Decimal(str(proj.get('agricultural_sales', 0)))
                ecosystem_services = Decimal(str(proj.get('ecosystem_services', 0)))
                subsidies_incentives = Decimal(str(proj.get('subsidies_incentives', 0)))
                total_costs = Decimal(str(proj.get('total_costs', 0)))
                
                total_revenue = agricultural_sales + ecosystem_services + subsidies_incentives
                net_cash_flow = total_revenue - total_costs
                
                yearly_financials.append(YearlyFinancials(
                    year=year,
                    total_revenue=total_revenue,
                    total_costs=total_costs,
                    net_cash_flow=net_cash_flow,
                    agricultural_sales=agricultural_sales,
                    ecosystem_services=ecosystem_services,
                    subsidies_incentives=subsidies_incentives
                ))
            
            if len(yearly_financials) < 10:
                yearly_financials = self._extrapolate_missing_years(yearly_financials, 10)
            
            total_revenue_10_year = sum(year.total_revenue for year in yearly_financials)
            total_costs_10_year = sum(year.total_costs for year in yearly_financials)
            total_net_cash_flow_10_year = total_revenue_10_year - total_costs_10_year
            
            return PropertyEstimateResponse(
                project_name=project_name,
                project_description=project_description,
                location=location,
                area_hectares=area_hectares,
                yearly_financials=yearly_financials,
                total_revenue_10_year=total_revenue_10_year,
                total_costs_10_year=total_costs_10_year,
                total_net_cash_flow_10_year=total_net_cash_flow_10_year
            )
            
        except Exception as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            logger.error(f"Response text: {response_text}")
            
            return self._create_fallback_response(request)
    
    def _extrapolate_missing_years(self, existing_years: List[YearlyFinancials], target_years: int) -> List[YearlyFinancials]:
        
        """Fill in missing years with reasonable extrapolations"""
        
        if not existing_years: return []
        complete_years = existing_years.copy()
        
        while len(complete_years) < target_years:
            
            last_year = complete_years[-1]
            next_year_num = last_year.year + 1
            growth_rate = 1.05  # 5% growth
            agricultural_sales = last_year.agricultural_sales * growth_rate
            ecosystem_services = last_year.ecosystem_services * Decimal('1.1')  # Higher growth for ecosystem services
            subsidies_incentives = last_year.subsidies_incentives * Decimal('0.95')  # Declining subsidies
            total_costs = last_year.total_costs * Decimal('1.02')  # Modest cost increases
            
            total_revenue = agricultural_sales + ecosystem_services + subsidies_incentives
            net_cash_flow = total_revenue - total_costs
            
            complete_years.append(YearlyFinancials(
                year=next_year_num,
                total_revenue=total_revenue,
                total_costs=total_costs,
                net_cash_flow=net_cash_flow,
                agricultural_sales=agricultural_sales,
                ecosystem_services=ecosystem_services,
                subsidies_incentives=subsidies_incentives
            ))
        
        return complete_years[:target_years]
    
    def _create_fallback_response(self, request: PropertyEstimateRequest) -> PropertyEstimateResponse:
        logger.warning("Using fallback response due to OpenAI parsing failure")
        mock_service = MockPropertyEstimateAI()
        return mock_service._generate_detailed_estimate(request)
    
    def _format_location(self, address: str) -> str: 
        parts = address.split(',')
        if len(parts) >= 2:
            return f"{parts[0].strip()}, {parts[-1].strip()}"
        return address.strip()


class MockPropertyEstimateAI:
    
    def __init__(self):
        self.model = "mock-ai-v1"
        logger.info("Using Mock AI service for detailed financial projections")
    
    async def generate_estimate(self, request: PropertyEstimateRequest):

        start_time = time.time()        
        await asyncio.sleep(random.uniform(2, 5))
        
        try:
            mock_data = self._generate_detailed_estimate(request)
            processing_time = time.time() - start_time
            
            logger.info(f"Mock AI estimate generated in {processing_time:.2f}s for {request.address}")
            
            raw_response = {
                'project_name': mock_data.project_name,
                'project_description': mock_data.project_description,
                'location': mock_data.location,
                'area_hectares': str(mock_data.area_hectares),
                'yearly_financials': [
                    {
                        'year': year.year,
                        'total_revenue': str(year.total_revenue),
                        'total_costs': str(year.total_costs),
                        'net_cash_flow': str(year.net_cash_flow),
                        'agricultural_sales': str(year.agricultural_sales),
                        'ecosystem_services': str(year.ecosystem_services),
                        'subsidies_incentives': str(year.subsidies_incentives)
                    }
                    for year in mock_data.yearly_financials
                ],
                'total_revenue_10_year': str(mock_data.total_revenue_10_year),
                'total_costs_10_year': str(mock_data.total_costs_10_year),
                'total_net_cash_flow_10_year': str(mock_data.total_net_cash_flow_10_year),
                'processing_time_seconds': processing_time,
                'model_used': self.model,
            }
            
            return mock_data, raw_response
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Mock AI estimation failed: {str(e)}"
            logger.error(f"{error_msg} (processing_time: {processing_time:.2f}s)")
            raise AIEstimationError(error_msg, processing_time)
    
    def _generate_detailed_estimate(self, request: PropertyEstimateRequest) -> PropertyEstimateResponse:
        
        lot_size_acres = float(request.lot_size)
        lot_size_hectares = lot_size_acres * 0.404686
        
        location = self._format_location(request.address)
        
        project_names = [
            f"Regenerative Agricultural Initiative",
            f"Sustainable Farming Project", 
            f"Carbon Sequestration Agriculture Program",
            f"Biodiversity Enhancement Farm",
            f"Soil Restoration Project"
        ]
        
        project_name = random.choice(project_names)
        description = f"This {lot_size_hectares:.1f}-hectare regenerative agriculture project focuses on sustainable farming practices, soil restoration, and carbon sequestration. The initiative combines modern agricultural techniques with environmental stewardship to create a profitable and sustainable farming operation. Key components include cover crop rotation, integrated pest management, livestock integration, and agroforestry systems. The project is designed to improve soil health, increase biodiversity, and generate multiple revenue streams while contributing to climate change mitigation through carbon sequestration."
        yearly_financials = []
        
        for year in range(1, 11):
            
            growth_factor = 1 + (year - 1) * 0.15
            base_ag_sales = lot_size_hectares * random.uniform(800, 1500) * growth_factor
            agricultural_sales = Decimal(str(int(base_ag_sales)))
            ecosystem_base = lot_size_hectares * random.uniform(50, 200) * (growth_factor ** 1.5)
            
            if year <= 2: ecosystem_services = Decimal("0")
            else: ecosystem_services = Decimal(str(int(ecosystem_base)))
            
            if year <= 5: subsidies = Decimal(str(int(lot_size_hectares * random.uniform(40, 80))))
            else: subsidies = Decimal(str(int(lot_size_hectares * random.uniform(20, 40))))
            
            total_revenue = agricultural_sales + ecosystem_services + subsidies
            cost_factor = 1.1 - (year - 1) * 0.02
            base_costs = lot_size_hectares * random.uniform(600, 1000) * cost_factor
            total_costs = Decimal(str(int(base_costs)))
            net_cash_flow = total_revenue - total_costs
            
            yearly_financials.append(YearlyFinancials(
                year=year,
                total_revenue=total_revenue,
                total_costs=total_costs,
                net_cash_flow=net_cash_flow,
                agricultural_sales=agricultural_sales,
                ecosystem_services=ecosystem_services,
                subsidies_incentives=subsidies
            ))
        
        total_revenue_10_year = sum(year.total_revenue for year in yearly_financials)
        total_costs_10_year = sum(year.total_costs for year in yearly_financials)
        total_net_cash_flow_10_year = total_revenue_10_year - total_costs_10_year
        
        return PropertyEstimateResponse(
            project_name=project_name,
            project_description=description,
            location=location,
            area_hectares=Decimal(str(round(lot_size_hectares, 1))),
            yearly_financials=yearly_financials,
            total_revenue_10_year=total_revenue_10_year,
            total_costs_10_year=total_costs_10_year,
            total_net_cash_flow_10_year=total_net_cash_flow_10_year
        )
    
    def _format_location(self, address: str) -> str:
        parts = address.split(',')
        if len(parts) >= 2: return f"{parts[0].strip()}, {parts[-1].strip()}"
        return address.strip()


class FallbackPropertyEstimateAI:
    
    def __init__(self):
        self.production_service = None
        self.mock_service = MockPropertyEstimateAI()
        self.use_production = False
        
        try:
            if (hasattr(settings, 'OPENAI_API_KEY') and 
                settings.OPENAI_API_KEY and 
                settings.OPENAI_API_KEY.startswith('sk-') and
                len(settings.OPENAI_API_KEY) > 20):
                
                self.production_service = ProductionPropertyEstimateAI()
                self.use_production = True
                logger.info("OpenAI production service initialized. Will try OpenAI first, fallback to mock on errors.")
            else:
                logger.info("Invalid or missing OpenAI API key. Using mock service only.")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI service: {e}. Using mock service only.")
    
    async def generate_estimate(self, request: PropertyEstimateRequest):
        
        # If no production service available, use mock directly
        if not self.use_production or not self.production_service:
            logger.info("Using mock AI service (no OpenAI available)")
            return await self.mock_service.generate_estimate(request)
        
        # Try production service first
        try:
            logger.info("Attempting OpenAI production service...")
            return await self.production_service.generate_estimate(request)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                logger.warning("OpenAI quota exceeded. Using mock service as fallback.")
            elif "401" in error_str or "authentication" in error_str.lower():
                logger.warning("OpenAI authentication failed. Check your API key. Using mock service.")
            elif "insufficient_quota" in error_str.lower():
                logger.warning("OpenAI account has insufficient credits. Using mock service.")
            else:
                logger.warning(f"OpenAI service failed: {error_str}. Using mock service as fallback.")
            
            # Fall back to mock service
            return await self.mock_service.generate_estimate(request)


class AIEstimationError(Exception):
    
    def __init__(self, message: str, processing_time: float):
        self.message = message
        self.processing_time = processing_time
        super().__init__(self.message)


def get_ai_service():
    try:
        return FallbackPropertyEstimateAI()
    except Exception as e:
        logger.error(f"Failed to initialize fallback AI service: {e}. Using basic mock.")
        return MockPropertyEstimateAI()


ai_service = get_ai_service()