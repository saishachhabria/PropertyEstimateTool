from django import forms
from django.core.validators import MinValueValidator
from .models import PropertyInquiry
from decimal import Decimal


class PropertyEstimateForm(forms.ModelForm):
    
    UNIT_CHOICES = [
        ('acres', 'acres'),
        ('hectares', 'hectares'),
    ]
    
    lot_size = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 bg-gray-100 rounded-lg border-none focus:bg-white focus:ring-2 focus:ring-green-500 transition-all',
            'placeholder': '24',
            'min': '0.01',
            'step': '0.01',
        }),
        label='Land Plot Size'
    )
    
    unit = forms.ChoiceField(
        choices=UNIT_CHOICES,
        initial='acres',
        widget=forms.Select(attrs={
            'class': 'bg-gray-100 px-2 py-1 rounded text-sm border-none focus:outline-none',
        })
    )
    
    class Meta:
        model = PropertyInquiry
        fields = ['address', 'lot_size', 'user_context']
        
        widgets = {
            'address': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 bg-gray-100 rounded-lg border-none focus:bg-white focus:ring-2 focus:ring-green-500 transition-all',
                'placeholder': 'São José do Rio Preto, Brazil',
            }),
            'user_context': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 bg-gray-100 rounded-lg border-none focus:bg-white focus:ring-2 focus:ring-green-500 transition-all resize-none',
                'placeholder': 'Tell us about your goals, experience, or any specific requirements...',
                'rows': 3,
            }),
        }
        
        labels = {
            'address': 'Land plot address or region',
            'user_context': 'Additional Context (Optional)',
        }
        
        help_texts = {
            'address': 'Enter the location or address of your property',
            'lot_size': 'Enter the size of your land plot',
            'user_context': 'Any additional information about your goals or requirements',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['address'].error_messages.update({
            'required': 'Property address is required',
            'max_length': 'Address is too long (maximum 500 characters)',
        })
        
        self.fields['lot_size'].error_messages.update({
            'required': 'Lot size is required',
            'invalid': 'Please enter a valid number',
            'min_value': 'Lot size must be at least 0.01 acres',
        })
    
    def clean_address(self):
        address = self.cleaned_data.get('address')
        if address:
            address = address.strip()
            if len(address) < 5: 
                raise forms.ValidationError('Address must be at least 5 characters long')
        return address
    
    def clean_lot_size(self):
        lot_size = self.cleaned_data.get('lot_size')
        unit = self.data.get('unit', 'acres')
        if lot_size and unit == 'hectares': lot_size = lot_size * Decimal('2.47105')
        return lot_size
    
    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class QuestionnaireResponseForm(forms.Form):
    
    response = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'response-input',
            'placeholder': 'Share your thoughts here...',
        })
    )
    
    def __init__(self, *args, question_data=None, **kwargs):
        super().__init__(*args, **kwargs)
        if question_data:
            self.fields['response'].required = question_data.get('required', True)
            self.fields['response'].widget.attrs['placeholder'] = question_data.get('placeholder', 'Share your thoughts here...')
    
    def clean_response(self):
        response = self.cleaned_data.get('response', '').strip()
        if not response: raise forms.ValidationError('Please provide a response.')
        if len(response) < 5: raise forms.ValidationError('Response must be at least 5 characters long.')
        return response
