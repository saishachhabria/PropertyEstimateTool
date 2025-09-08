import uuid
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class PropertyInquiry(models.Model):
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    address = models.CharField(max_length=500, help_text="Property address or location")
    lot_size = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Lot size in acres"
    )
    user_context = models.TextField(blank=True, null=True, help_text="Additional user context")
    
    # Questionnaire tracking
    current_question = models.IntegerField(default=1)
    questionnaire_completed = models.BooleanField(default=False)
    questionnaire_responses = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Property Inquiry"
        verbose_name_plural = "Property Inquiries"
    
    def __str__(self):
        return f"Inquiry for {self.address[:50]} ({self.lot_size} acres)"
    
    def get_progress_percentage(self):
        """Calculate questionnaire completion percentage"""
        return min((self.current_question / 4) * 100, 100)
    
    @property
    def is_questionnaire_complete(self):
        """Check if questionnaire is complete"""
        return self.questionnaire_completed


class PropertyEstimate(models.Model):
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    inquiry = models.OneToOneField(
        'PropertyInquiry', 
        on_delete=models.CASCADE,
        related_name='estimate'
    )
    
    # Basic project info - with defaults and null handling
    project_name = models.CharField(max_length=200, blank=True, default='')
    project_description = models.TextField(blank=True, default='')
    location = models.CharField(max_length=200, blank=True, default='')
    area_hectares = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    
    total_revenue_10_year = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    total_costs_10_year = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    total_net_cash_flow_10_year = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    
    yearly_financials = models.JSONField(default=list, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    ai_model_used = models.CharField(max_length=50, blank=True, default='mock-ai-v1')
    processing_time_seconds = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True, default='')  # Fixed: added default
    raw_ai_response = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Estimate for {self.inquiry.address} - {self.project_name}"
    
    @property
    def roi_percentage(self):
        """Calculate 10-year ROI percentage"""
        if self.total_costs_10_year and self.total_costs_10_year > 0:
            roi = (self.total_net_cash_flow_10_year / self.total_costs_10_year) * 100
            return float(roi)
        return None
    
    def get_yearly_data(self):
        """Get yearly financial data as structured objects"""
        return self.yearly_financials if self.yearly_financials else []
    
    def get_revenue_breakdown(self, year=None):
        """Get revenue breakdown for a specific year or all years"""
        if not self.yearly_financials:
            return {}
            
        if year:
            
            for year_data in self.yearly_financials:
                if year_data.get('year') == year:
                    return {
                        'agricultural_sales': year_data.get('agricultural_sales', 0),
                        'ecosystem_services': year_data.get('ecosystem_services', 0), 
                        'subsidies_incentives': year_data.get('subsidies_incentives', 0)
                    }
            return {}
        else:
            
            totals = {
                'agricultural_sales': 0,
                'ecosystem_services': 0,
                'subsidies_incentives': 0
            }
            
            for year_data in self.yearly_financials:
                totals['agricultural_sales'] += Decimal(str(year_data.get('agricultural_sales', 0)))
                totals['ecosystem_services'] += Decimal(str(year_data.get('ecosystem_services', 0)))
                totals['subsidies_incentives'] += Decimal(str(year_data.get('subsidies_incentives', 0)))
            
            return totals
    
    def get_chart_data(self):
        """Get data formatted for charts"""
        if not self.yearly_financials:
            return []
            
        chart_data = []
        for year_data in self.yearly_financials:
            chart_data.append({
                'year': year_data.get('year'),
                'net_cash_flow': float(year_data.get('net_cash_flow', 0)),
                'total_revenue': float(year_data.get('total_revenue', 0)),
                'total_costs': float(year_data.get('total_costs', 0)),
                'agricultural_sales': float(year_data.get('agricultural_sales', 0)),
                'ecosystem_services': float(year_data.get('ecosystem_services', 0)),
                'subsidies_incentives': float(year_data.get('subsidies_incentives', 0))
            })
        
        return chart_data
    

# Hardcoded questions data - 4 questions matching mockup
QUESTIONNAIRE_QUESTIONS = {
    1: {
        'title': "What's your goal with your property?",
        'placeholder': "I want to become much more profitable and have healthy land where I can grow those things on it",
        'required': True
    },
    2: {
        'title': "What's currently on your property?",
        'placeholder': "I currently have 6 hectares of cattle (around 40 cows) and the rest is mostly vacant", 
        'required': True
    },
    3: {
        'title': "How much time and money are you willing to invest?",
        'placeholder': "I don't have a lot of time but I'd be willing to hire someone to help me out",
        'required': True
    },
    4: {
        'title': "Almost ready! Anything you're really excited about? Or even not excited about?",
        'placeholder': "I feel I'm really interested in shifting more focus to the property. And I think that I love how it's connected to local",
        'required': False
    }
}


def get_question(number):
    """Get question data by number"""
    return QUESTIONNAIRE_QUESTIONS.get(number)