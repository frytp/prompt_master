"""
Admin configuration for Prompt Manager models.
"""
from django.contrib import admin
from .models import Category, Tag, AIModel, Prompt


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""
    
    list_display = ['name', 'color', 'prompt_count']
    search_fields = ['name', 'description']
    
    def prompt_count(self, obj):
        """Display number of prompts in this category."""
        return obj.prompts.count()
    prompt_count.short_description = 'Количество промптов'


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin interface for Tag model."""
    
    list_display = ['name', 'prompt_count']
    search_fields = ['name', 'description']
    
    def prompt_count(self, obj):
        """Display number of prompts with this tag."""
        return obj.prompts.count()
    prompt_count.short_description = 'Количество промптов'


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    """Admin interface for AIModel."""
    
    list_display = ['name', 'version', 'prompt_count']
    search_fields = ['name', 'version']
    list_filter = ['version']
    
    def prompt_count(self, obj):
        """Display number of prompts for this AI model."""
        return obj.prompts.count()
    prompt_count.short_description = 'Количество промптов'


@admin.register(Prompt)
class PromptAdmin(admin.ModelAdmin):
    """Admin interface for Prompt model."""
    
    list_display = ['title', 'category', 'is_default', 'usage_count', 
                    'created_at']
    list_filter = ['is_default', 'category', 'tags', 'ai_models', 
                   'created_at']
    search_fields = ['title', 'content']
    filter_horizontal = ['tags', 'ai_models']
    readonly_fields = ['created_at', 'updated_at', 'usage_count']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('title', 'content', 'category')
        }),
        ('Классификация', {
            'fields': ('tags', 'ai_models', 'is_default')
        }),
        ('Статистика', {
            'fields': ('usage_count', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )