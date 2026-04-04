"""
Forms for creating and editing prompts.
"""
from django import forms
from django.core.exceptions import ValidationError
import json
from .models import Prompt
from .constants import MAX_JSON_FILE_SIZE, MIN_TITLE_LENGTH, MIN_CONTENT_LENGTH


class PromptForm(forms.ModelForm):
    """Form for creating and editing prompt instances."""
    
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
                'placeholder': f'Введите текст промпта (минимум {MIN_CONTENT_LENGTH} символов)'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tags': forms.CheckboxSelectMultiple(),
            'ai_models': forms.CheckboxSelectMultiple(),
        }
    
    def clean_title(self):
        """Validate prompt title."""
        title_value = self.cleaned_data.get('title', '').strip()
        
        if not title_value:
            raise ValidationError('Название не может быть пустым')
        
        if len(title_value) < MIN_TITLE_LENGTH:
            raise ValidationError(
                f'Название слишком короткое (минимум {MIN_TITLE_LENGTH} символа)'
            )
        
        return title_value
    
    def clean_content(self):
        """Validate prompt content."""
        content_value = self.cleaned_data.get('content', '').strip()
        
        if not content_value:
            raise ValidationError('Текст промпта не может быть пустым')
        
        if len(content_value) < MIN_CONTENT_LENGTH:
            raise ValidationError(
                f'Текст промпта слишком короткий (минимум {MIN_CONTENT_LENGTH} символов)'
            )
        
        return content_value
    
    def clean(self):
        """Perform form-level validation."""
        cleaned_data = super().clean()
        selected_models = cleaned_data.get('ai_models')
        
        if not selected_models or selected_models.count() == 0:
            raise ValidationError(
                'Выберите хотя бы одну AI модель для промпта'
            )
        
        return cleaned_data


class ImportPromptsForm(forms.Form):
    """Form for importing prompts from JSON file."""
    
    json_file = forms.FileField(
        label='JSON файл',
        help_text=f'Загрузите файл с промптами в формате JSON (макс. {MAX_JSON_FILE_SIZE // (1024 * 1024)} МБ)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.json'
        })
    )
    
    def clean_json_file(self):
        """Validate uploaded JSON file."""
        uploaded_file = self.cleaned_data.get('json_file')
        
        if not uploaded_file:
            raise ValidationError('Файл не загружен')
        
        # Check file size
        if uploaded_file.size > MAX_JSON_FILE_SIZE:
            raise ValidationError(
                f'Файл слишком большой. Максимальный размер: {MAX_JSON_FILE_SIZE // (1024 * 1024)} МБ'
            )
        
        # Check file extension
        if not uploaded_file.name.endswith('.json'):
            raise ValidationError('Загрузите файл в формате JSON')
        
        # Validate JSON structure
        try:
            file_content = uploaded_file.read().decode('utf-8')
            data = json.loads(file_content)
            
            if not isinstance(data, list):
                raise ValidationError(
                    'Неверная структура JSON. Ожидается массив объектов'
                )
            
            # Reset file pointer for later use
            uploaded_file.seek(0)
            
        except json.JSONDecodeError:
            raise ValidationError('Неверный формат JSON')
        except UnicodeDecodeError:
            raise ValidationError('Ошибка кодировки файла. Используйте UTF-8')
        
        return uploaded_file