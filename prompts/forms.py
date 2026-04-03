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
        
class ImportPromptsForm(forms.Form):
    """Form for importing prompts from JSON file."""
    
    json_file = forms.FileField(
        label='JSON файл',
        help_text='Загрузите файл с промптами в формате JSON (макс. 5 МБ)',
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
        
        # Check file size (5 MB max)
        max_size = 5 * 1024 * 1024  # 5 MB
        if uploaded_file.size > max_size:
            raise ValidationError(
                f'Файл слишком большой. Максимальный размер: 5 МБ'
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