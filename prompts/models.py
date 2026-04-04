"""
Models for Prompt Manager application.
"""

from django.db import models
from django.core.validators import MinLengthValidator


class Category(models.Model):
    """Category for organizing prompts (e.g., Education, Programming)."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название категории"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )
    color = models.CharField(
        max_length=7,
        default="#3498db",
        verbose_name="Цвет (hex)",
        help_text="Например: #3498db"
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tag for categorizing prompts (e.g., explanation, code, translation)."""
    
    name = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Название тега"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ['name']

    def __str__(self):
        return self.name


class AIModel(models.Model):
    """AI model that can use prompts (e.g., ChatGPT, Claude)."""
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название AI модели"
    )
    version = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Версия"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )

    class Meta:
        verbose_name = "AI Модель"
        verbose_name_plural = "AI Модели"
        ordering = ['name']

    def __str__(self):
        if self.version:
            return f"{self.name} ({self.version})"
        return self.name


class Collection(models.Model):
    """Collection (folder) for organizing prompts."""
    
    name = models.CharField(
        max_length=200,
        verbose_name="Название коллекции"
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )
    color = models.CharField(
        max_length=7,
        default="#9b59b6",
        verbose_name="Цвет (hex)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )

    class Meta:
        verbose_name = "Коллекция"
        verbose_name_plural = "Коллекции"
        ordering = ['name']

    def __str__(self):
        return self.name


class Prompt(models.Model):
    """Main model for storing prompt templates."""
    
    title = models.CharField(
        max_length=200,
        verbose_name="Название",
        validators=[MinLengthValidator(3)]
    )
    content = models.TextField(
        verbose_name="Текст промпта",
        validators=[MinLengthValidator(10)],
        help_text="Минимум 10 символов"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prompts',
        verbose_name="Категория"
    )
    collection = models.ForeignKey(
        Collection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prompts',
        verbose_name="Коллекция"
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='prompts',
        blank=True,
        verbose_name="Теги"
    )
    ai_models = models.ManyToManyField(
        AIModel,
        related_name='prompts',
        blank=True,
        verbose_name="AI Модели"
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name="Предустановленный",
        help_text="Промпт по умолчанию (нельзя удалить)"
    )
    is_favorite = models.BooleanField(
        default=False,
        verbose_name="Избранное"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата изменения"
    )
    usage_count = models.IntegerField(
        default=0,
        verbose_name="Количество использований"
    )

    class Meta:
        verbose_name = "Промпт"
        verbose_name_plural = "Промпты"
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def increment_usage(self):
        """Increment usage counter when prompt is copied."""
        self.usage_count += 1
        self.save(update_fields=['usage_count'])


class PromptVariable(models.Model):
    """Store variable substitutions history for prompts."""
    
    prompt = models.ForeignKey(
        Prompt,
        on_delete=models.CASCADE,
        related_name='variables',
        verbose_name="Промпт"
    )
    variable_name = models.CharField(
        max_length=100,
        verbose_name="Название переменной"
    )
    value = models.TextField(
        verbose_name="Значение"
    )
    used_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата использования"
    )

    class Meta:
        verbose_name = "Переменная промпта"
        verbose_name_plural = "Переменные промптов"
        ordering = ['-used_at']

    def __str__(self):
        return f"{self.prompt.title} - {self.variable_name}"