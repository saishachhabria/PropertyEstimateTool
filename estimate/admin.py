# admin.py - Fixed to work with hardcoded questions (no QuestionnaireQuestion model)

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import PropertyInquiry, PropertyEstimate


@admin.register(PropertyInquiry)
class PropertyInquiryAdmin(admin.ModelAdmin):
    """Admin interface for Property Inquiries"""
    
    list_display = [
        'address_short', 
        'lot_size', 
        'questionnaire_status',
        'has_estimate',
        'created_at'
    ]
    list_filter = [
        'questionnaire_completed',
        'created_at',
        'lot_size',
    ]
    search_fields = [
        'address', 
        'user_context'
    ]
    readonly_fields = [
        'id', 
        'created_at', 
        'updated_at',
        'questionnaire_responses_formatted'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Property Details', {
            'fields': ('address', 'lot_size', 'user_context')
        }),
        ('Questionnaire Progress', {
            'fields': ('current_question', 'questionnaire_completed', 'questionnaire_responses_formatted'),
            'classes': ('wide',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def address_short(self, obj):
        """Display shortened address"""
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_short.short_description = 'Address'
    
    def questionnaire_status(self, obj):
        """Show questionnaire completion status"""
        if obj.questionnaire_completed:
            return format_html('<span style="color: green;">✓ Completed</span>')
        else:
            progress = obj.get_progress_percentage()
            return format_html(
                '<span style="color: orange;">📄 {}% (Q{})</span>', 
                int(progress), 
                obj.current_question
            )
    questionnaire_status.short_description = 'Questionnaire Status'
    
    def has_estimate(self, obj):
        """Show if inquiry has an estimate"""
        try:
            estimate = obj.estimate
            if estimate.status == 'completed':
                return format_html('<span style="color: green;">✓ Completed</span>')
            elif estimate.status == 'failed':
                return format_html('<span style="color: red;">✗ Failed</span>')
            else:
                return format_html('<span style="color: orange;">⏳ Pending</span>')
        except PropertyEstimate.DoesNotExist:
            return format_html('<span style="color: gray;">— None</span>')
    has_estimate.short_description = 'Estimate Status'
    
    def questionnaire_responses_formatted(self, obj):
        """Display formatted questionnaire responses"""
        if not obj.questionnaire_responses:
            return "No responses yet"
        
        from .models import get_question  # Import the function
        
        html_parts = []
        for question_num, response in obj.questionnaire_responses.items():
            try:
                question_data = get_question(int(question_num))
                if question_data:
                    question_title = question_data['title']
                    html_parts.append(f"<strong>Q{question_num}: {question_title}</strong><br/>")
                else:
                    html_parts.append(f"<strong>Q{question_num}:</strong><br/>")
                    
                response_text = str(response)[:100]
                if len(str(response)) > 100:
                    response_text += "..."
                html_parts.append(f"{response_text}<br/><br/>")
            except (ValueError, TypeError):
                html_parts.append(f"<strong>Q{question_num}:</strong> {response}<br/><br/>")
        
        return format_html("".join(html_parts))
    questionnaire_responses_formatted.short_description = 'Questionnaire Responses'


@admin.register(PropertyEstimate)
class PropertyEstimateAdmin(admin.ModelAdmin):
    """Admin interface for Property Estimates"""
    
    list_display = [
        'project_name_short',
        'inquiry_address_short',
        'total_net_cash_flow_10_year',
        'roi_display',
        'status',
        'ai_model_used',
        'created_at'
    ]
    list_filter = [
        'status',
        'ai_model_used',
        'created_at',
        'inquiry__lot_size'
    ]
    search_fields = [
        'project_name',
        'project_description',
        'inquiry__address'
    ]
    readonly_fields = [
        'id',
        'processing_time_seconds',
        'raw_ai_response_formatted',
        'created_at',
        'updated_at',
        'roi_percentage'
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        ('Project Information', {
            'fields': ('inquiry', 'project_name', 'project_description', 'location', 'area_hectares')
        }),
        ('10-Year Financial Summary', {
            'fields': (
                'total_net_cash_flow_10_year',
                'total_revenue_10_year', 
                'total_costs_10_year',
                'roi_percentage'
            )
        }),
        ('Processing Details', {
            'fields': (
                'status',
                'ai_model_used',
                'processing_time_seconds',
                'error_message'
            )
        }),
        ('Raw Data', {
            'fields': ('raw_ai_response_formatted',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def project_name_short(self, obj):
        """Display shortened project name"""
        if obj.project_name:
            return obj.project_name[:40] + '...' if len(obj.project_name) > 40 else obj.project_name
        return '—'
    project_name_short.short_description = 'Project Name'
    
    def inquiry_address_short(self, obj):
        """Display shortened inquiry address"""
        address = obj.inquiry.address
        return address[:30] + '...' if len(address) > 30 else address
    inquiry_address_short.short_description = 'Property Address'
    
    def roi_display(self, obj):
        """Display ROI percentage"""
        roi = obj.roi_percentage
        if roi is not None:
            color = 'green' if roi > 0 else 'red'
            return format_html('<span style="color: {};">{:.1f}%</span>', color, roi)
        return '—'
    roi_display.short_description = 'ROI %'
    
    def raw_ai_response_formatted(self, obj):
        """Display formatted raw AI response"""
        if not obj.raw_ai_response:
            return "No raw response data"
        
        import json
        try:
            formatted_json = json.dumps(obj.raw_ai_response, indent=2)
            return format_html('<pre style="font-size: 12px; max-height: 300px; overflow-y: auto;">{}</pre>', formatted_json)
        except:
            return str(obj.raw_ai_response)
    raw_ai_response_formatted.short_description = 'Raw AI Response'
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly after creation"""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.extend([
                'inquiry',
                'total_net_cash_flow_10_year',
                'total_revenue_10_year',
                'total_costs_10_year'
            ])
        return readonly
    
    def has_add_permission(self, request):
        """Disable manual creation of estimates"""
        return False


# Customize admin site
admin.site.site_header = "Valora Earth Property Estimates"
admin.site.site_title = "Valora Earth Admin"
admin.site.index_title = "Property Estimate Management"