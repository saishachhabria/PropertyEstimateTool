import asyncio
import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.generic import FormView, View
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async

from .models import PropertyInquiry, PropertyEstimate, get_question
from .forms import PropertyEstimateForm
from .ai_service import ai_service, PropertyEstimateRequest, AIEstimationError

logger = logging.getLogger(__name__)


class PropertyEstimateView(FormView):
    
    template_name = 'form.html'
    form_class = PropertyEstimateForm
    
    def form_valid(self, form):
        
        try:
            inquiry = form.save(commit=False)
            inquiry.save()
            logger.info(f"Created property inquiry {inquiry.id} for {inquiry.address}")
            return redirect(f'/estimate/questionnaire/{inquiry.id}/1/')
                
        except Exception as e:
            logger.error(f"Error creating property inquiry: {e}")
            form.add_error(None, "An error occurred while processing your request. Please try again.")
            return self.form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Estimate Your Earnings'
        return context


class QuestionnaireView(View):
    
    template_name = 'questionnaire.html'
    
    def dispatch(self, request, *args, **kwargs):    
        self.inquiry = get_object_or_404(PropertyInquiry, id=kwargs['inquiry_id'])
        self.question_number = kwargs.get('question', 1)
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        
        if self.inquiry.questionnaire_completed:
            return redirect(f'/estimate/processing/{self.inquiry.id}/')
        
        if self.question_number < 1 or self.question_number > 4:
            return redirect(f'/estimate/questionnaire/{self.inquiry.id}/1/')
        
        question_data = get_question(self.question_number)
        if not question_data:
            return redirect(f'/estimate/questionnaire/{self.inquiry.id}/1/')
        
        current_response = self.inquiry.questionnaire_responses.get(str(self.question_number), '')
        
        context = {
            'question_number': self.question_number,
            'question_data': question_data,
            'inquiry': self.inquiry,
            'current_response': current_response,
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        
        response = request.POST.get('response', '').strip()
        
        question_data = get_question(self.question_number)
        if not question_data:
            return redirect(f'/estimate/questionnaire/{self.inquiry.id}/1/')
        
        if question_data['required'] and not response:
            messages.error(request, "This question requires a response.")
            return self.get(request, *args, **kwargs)
        
        if not self.inquiry.questionnaire_responses:
            self.inquiry.questionnaire_responses = {}
        
        self.inquiry.questionnaire_responses[str(self.question_number)] = response
        self.inquiry.current_question = self.question_number
        self.inquiry.save()
        
        logger.info(f"Saved response for question {self.question_number}: {response[:50]}...")
        
        if self.question_number >= 4:
            self.inquiry.questionnaire_completed = True
            self.inquiry.save()
            logger.info(f"Questionnaire completed for inquiry {self.inquiry.id}")
            return redirect(f'/estimate/processing/{self.inquiry.id}/')
        else:
            next_question = self.question_number + 1
            return redirect(f'/estimate/questionnaire/{self.inquiry.id}/{next_question}/')


class ProcessingView(View):
    
    template_name = 'waiting.html'
    
    def get(self, request, inquiry_id):
        
        inquiry = get_object_or_404(PropertyInquiry, id=inquiry_id)
        
        try:
            estimate = inquiry.estimate
            if estimate.status == 'completed':
                return redirect(f'/estimate/results/{inquiry_id}/')
            elif estimate.status == 'failed':
                messages.error(request, "Estimate generation failed. Please try again.")
                return redirect('/estimate/')
        except PropertyEstimate.DoesNotExist: pass
        
        context = { 'inquiry': inquiry }
        
        return render(request, self.template_name, context)


class GenerateEstimateView(View):
    
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, inquiry_id):
        
        inquiry = get_object_or_404(PropertyInquiry, id=inquiry_id)
        
        try:
            
            estimate, created = PropertyEstimate.objects.get_or_create(
                inquiry=inquiry,
                defaults={'status': 'pending'}
            )
            
            if estimate.status == 'completed':
                return JsonResponse({
                    'status': 'completed',
                    'redirect_url': f'/estimate/results/{inquiry_id}/'
                })
            
            user_context = inquiry.user_context or ""
            
            if inquiry.questionnaire_responses:
                responses_text = "\n".join([
                    f"Q{num}: {response}" 
                    for num, response in inquiry.questionnaire_responses.items()
                ])
                user_context += f"\n\nQuestionnaire Responses:\n{responses_text}"
            
            from .ai_service import PropertyEstimateRequest
            
            ai_request = PropertyEstimateRequest(
                address=inquiry.address,
                lot_size=inquiry.lot_size,
                user_context=user_context
            )
            
            estimate.status = 'processing'
            estimate.save()
            
            try:
                
                result_data, raw_response = asyncio.run(ai_service.generate_estimate(ai_request))
                
                estimate.project_name = result_data.project_name
                estimate.project_description = result_data.project_description
                estimate.location = result_data.location
                estimate.area_hectares = result_data.area_hectares
                
                estimate.total_revenue_10_year = result_data.total_revenue_10_year
                estimate.total_costs_10_year = result_data.total_costs_10_year  
                estimate.total_net_cash_flow_10_year = result_data.total_net_cash_flow_10_year
                
                yearly_data = []
                for year_financial in result_data.yearly_financials:
                    yearly_data.append({
                        'year': year_financial.year,
                        'total_revenue': str(year_financial.total_revenue),
                        'total_costs': str(year_financial.total_costs),
                        'net_cash_flow': str(year_financial.net_cash_flow),
                        'agricultural_sales': str(year_financial.agricultural_sales),
                        'ecosystem_services': str(year_financial.ecosystem_services),
                        'subsidies_incentives': str(year_financial.subsidies_incentives)
                    })
                
                estimate.yearly_financials = yearly_data
        
                estimate.raw_ai_response = raw_response
                estimate.processing_time_seconds = raw_response.get('processing_time_seconds', 0)
                estimate.ai_model_used = raw_response.get('model_used', 'mock-ai-v1')
                estimate.status = 'completed'
                estimate.save()
                
                logger.info(f"Generated detailed estimate for inquiry {inquiry.id}: {result_data.project_name}")
                
                return JsonResponse({
                    'status': 'completed',
                    'redirect_url': f'/estimate/results/{inquiry_id}/'
                })
                
            except Exception as ai_error:
                estimate.status = 'failed'
                estimate.error_message = str(ai_error)
                
                if hasattr(ai_error, 'processing_time'):
                    estimate.processing_time_seconds = ai_error.processing_time
                
                estimate.save()
                
                logger.error(f"AI estimation failed for inquiry {inquiry.id}: {ai_error}")
                
                return JsonResponse({
                    'status': 'failed',
                    'error': str(ai_error)
                })
            
        except Exception as e:
            logger.error(f"Unexpected error generating estimate for inquiry {inquiry.id}: {e}")
            
            try:
                estimate = inquiry.estimate
                estimate.status = 'failed'
                estimate.error_message = str(e)
                estimate.save()
            except:
                pass
            
            return JsonResponse({
                'status': 'failed',
                'error': 'An unexpected error occurred. Please try again.'
            })
    
    def get(self, request, inquiry_id):
        return JsonResponse({'error': 'Method not allowed'}, status=405)

class ResultsView(View):
    
    template_name = 'results.html'
    
    def get(self, request, inquiry_id):
        """Display results page"""
        inquiry = get_object_or_404(PropertyInquiry, id=inquiry_id)
        
        try:
            estimate = inquiry.estimate
            if estimate.status != 'completed':
                messages.error(request, "Estimate is not ready yet.")
                return redirect(f'/estimate/processing/{inquiry_id}/')
        except PropertyEstimate.DoesNotExist:
            messages.error(request, "No estimate found for this inquiry.")
            return redirect('/estimate/')
        
        context = {
            'inquiry': inquiry,
            'estimate': estimate,
        }
        
        return render(request, self.template_name, context)

def health_check(request):
    
    return JsonResponse({
        'status': 'healthy',
        'version': '1.0.0',
        'ai_service': 'available' if ai_service else 'unavailable'
    })

def estimate_status(request, inquiry_id):
    
    inquiry = get_object_or_404(PropertyInquiry, id=inquiry_id)
    
    try:
        estimate = inquiry.estimate
        response_data = {
            'status': estimate.status,
            'progress': 0
        }
        
        if estimate.status == 'completed':
            response_data['progress'] = 100
            response_data['redirect_url'] = f'/estimate/results/{inquiry_id}/'
        elif estimate.status == 'processing':
            response_data['progress'] = 75
        elif estimate.status == 'failed':
            response_data['error'] = estimate.error_message or 'Unknown error occurred'
        
        return JsonResponse(response_data)
        
    except PropertyEstimate.DoesNotExist:
        return JsonResponse({
            'status': 'pending',
            'progress': 0
        })