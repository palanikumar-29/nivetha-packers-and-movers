from django import forms
from django.utils import timezone
from .models import QuoteRequest, MoveType, phone_validator


class QuoteForm(forms.ModelForm):
    website = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'})
    )

    class Meta:
        model = QuoteRequest
        fields = [
            'name',
            'phone',
            'move_type',
            'moving_from',
            'moving_to',
            'preferred_date',
            'details',
        ]
        widgets = {
            'move_type': forms.Select(choices=MoveType.choices),
            'preferred_date': forms.DateInput(attrs={'type': 'date'}),
            'details': forms.Textarea(attrs={'rows': 2}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '').strip()
        phone_validator(phone)
        return phone

    def clean_preferred_date(self):
        preferred_date = self.cleaned_data.get('preferred_date')
        if preferred_date:
            today = timezone.localdate()
            if preferred_date < today:
                raise forms.ValidationError("Preferred move date must be today or a future date.")
        return preferred_date

