"""
Forms for creating and editing prompts.
"""
import json

from django import forms
from django.core.exceptions import ValidationError

from .models import Prompt, Category, Tag, AIModel, Collection
from .constants import (
    MAX_JSON_FILE_SIZE,
    MIN_TITLE_LENGTH,
    MIN_CONTENT_LENGTH
)


class CollectionForm(forms.ModelForm):
    """Form for creating and editing collections."""
    class Meta:
        model = Collection
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название папки'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class PromptForm(forms.ModelForm):
    """Form for creating and editing prompt instances."""

    # Fields for creating new tags/models/categories on the fly
    new_tags = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите новые теги через запятую'
        }),
        label='Новые теги',
        help_text='Введите теги через запятую, например: важное, срочное'
    )

    new_ai_models = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите новые AI модели через запятую'
        }),
        label='Новые AI модели',
        help_text='Введите модели через запятую, например: GPT-4, Claude 3'
    )

    new_category = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Название новой категории'
        }),
        label='Новая категория',
        help_text='Если нужной категории нет в списке'
    )

    new_collection = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Название новой коллекции'
        }),
        label='Новая коллекция (папка)',
        help_text='Создать новую коллекцию для организации промптов'
    )

    class Meta:
        model = Prompt
        fields = [
            'title', 'content', 'category', 'collection',
            'tags', 'ai_models', 'is_favorite'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название промпта'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 10,
                'placeholder': (
                    f'Введите текст промпта (минимум {MIN_CONTENT_LENGTH} '
                    'символов)\nИспользуйте {{переменная}} для '
                    'создания шаблонов'
                )
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'collection': forms.Select(attrs={
                'class': 'form-select'
            }),
            'tags': forms.CheckboxSelectMultiple(),
            'ai_models': forms.CheckboxSelectMultiple(),
            'is_favorite': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
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

    def save(self, commit=True):
        """Save form and handle new tags/models/categories/collections."""
        instance = super().save(commit=False)

        # Handle new category
        new_category_name = self.cleaned_data.get('new_category', '').strip()
        if new_category_name:
            category, _ = Category.objects.get_or_create(
                name=new_category_name,
                defaults={
                    'description': f'Категория {new_category_name}',
                    'color': '#3498db'
                }
            )
            instance.category = category

        # Handle new collection
        new_col_name = self.cleaned_data.get('new_collection', '').strip()
        if new_col_name:
            collection, _ = Collection.objects.get_or_create(
                name=new_col_name,
                defaults={
                    'description': f'Коллекция {new_col_name}',
                    'color': '#9b59b6'
                }
            )
            instance.collection = collection

        if commit:
            instance.save()
            self.save_m2m()

            # Handle new tags
            new_tags_str = self.cleaned_data.get('new_tags', '').strip()
            if new_tags_str:
                new_tag_names = [t.strip() for t in new_tags_str.split(',') if t.strip()]
                for tag_name in new_tag_names:
                    tag, _ = Tag.objects.get_or_create(
                        name=tag_name,
                        defaults={'description': f'Тег {tag_name}'}
                    )
                    instance.tags.add(tag)

            # Handle new AI models
            new_models_str = self.cleaned_data.get('new_ai_models', '').strip()
            if new_models_str:
                new_model_names = [m.strip() for m in new_models_str.split(',') if m.strip()]
                for model_name in new_model_names:
                    model, _ = AIModel.objects.get_or_create(
                        name=model_name,
                        defaults={'description': f'AI модель {model_name}'}
                    )
                    instance.ai_models.add(model)

        return instance


class ImportPromptsForm(forms.Form):
    """Form for importing prompts from JSON file."""

    json_file = forms.FileField(
        label='JSON файл',
        help_text=(
            f'Загрузите файл с промптами в формате JSON '
            f'(макс. {MAX_JSON_FILE_SIZE // (1024 * 1024)} МБ)'
        ),
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.json'
        })
    )

    collection_name = forms.CharField(
        required=False,
        label='Название коллекции',
        help_text=(
            'Опционально: все импортированные промпты '
            'будут помещены в эту коллекцию'
        ),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: Промпты от пользователя X'
        })
    )

    def clean_json_file(self):
        """Validate uploaded JSON file."""
        uploaded_file = self.cleaned_data.get('json_file')
        if not uploaded_file:
            raise ValidationError('Файл не загружен')
        if uploaded_file.size > MAX_JSON_FILE_SIZE:
            raise ValidationError(
                f'Файл слишком большой. Максимальный размер: '
                f'{MAX_JSON_FILE_SIZE // (1024 * 1024)} МБ'
            )
        if not uploaded_file.name.endswith('.json'):
            raise ValidationError('Загрузите файл в формате JSON')

        try:
            file_content = uploaded_file.read().decode('utf-8')
            data = json.loads(file_content)
            if not isinstance(data, list):
                raise ValidationError('Неверная структура JSON. Ожидается массив объектов')
            uploaded_file.seek(0)
        except json.JSONDecodeError as exc:
            raise ValidationError('Неверный формат JSON') from exc
        except UnicodeDecodeError as exc:
            raise ValidationError('Ошибка кодировки файла. Используйте UTF-8') from exc

        return uploaded_file