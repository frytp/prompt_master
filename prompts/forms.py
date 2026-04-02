"""
Forms for Prompt Manager application.
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Prompt, Category, Tag, AIModel


class PromptForm(forms.ModelForm):
    """Form for creating and editing prompts."""
    
    class Meta:
        model = Prompt
        fields = ['title', 'content', 'category', 'tags', 'ai_models']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название промпта'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': 'Введите текст промпта (минимум 10 символов)'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tags': forms.CheckboxSelectMultiple(),
            'ai_models': forms.CheckboxSelectMultiple(),
        }
    
    def clean_title(self):
        """Validate title field."""
        title = self.cleaned_data.get('title')
        if not title:
            raise ValidationError('Название не может быть пустым')
        if len(title) < 3:
            raise ValidationError(
                'Название слишком короткое (минимум 3 символа)'
            )
        return title
    
    def clean_content(self):
        """Validate content field."""
        content = self.cleaned_data.get('content')
        if not content:
            raise ValidationError('Текст промпта не может быть пустым')
        if len(content) < 10:
            raise ValidationError(
                'Текст промпта слишком короткий (минимум 10 символов)'
            )
        return content
    
    def clean(self):
        """Additional form-level validation."""
        cleaned_data = super().clean()
        ai_models = cleaned_data.get('ai_models')
        
        # Проверка что выбрана хотя бы одна AI модель
        if not ai_models or ai_models.count() == 0:
            raise ValidationError(
                'Выберите хотя бы одну AI модель для промпта'
            )
        
        return cleaned_data