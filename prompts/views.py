from django.views.generic import (
    ListView, 
    DetailView, 
    CreateView, 
    UpdateView, 
    DeleteView,
    FormView
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
import json
from .models import Prompt, Category, Tag, AIModel
from .forms import PromptForm, ImportPromptsForm


class PromptListView(ListView):
    """Display paginated list of prompts with search and filters."""
    
    model = Prompt
    template_name = 'prompts/prompt_list.html'
    context_object_name = 'prompts'
    paginate_by = 12
    
    def get_queryset(self):
        """Get optimized queryset with search and filtering."""
        base_queryset = Prompt.objects.select_related(
            'category'
        ).prefetch_related(
            'tags', 
            'ai_models'
        )
        
        # Search by title
        search_term = self.request.GET.get('search', '').strip()
        if search_term:
            base_queryset = base_queryset.filter(
                title__icontains=search_term
            )
        
        # Filter by category
        cat_id = self.request.GET.get('category')
        if cat_id:
            base_queryset = base_queryset.filter(category_id=cat_id)
        
        # Filter by tag
        tag_id = self.request.GET.get('tag')
        if tag_id:
            base_queryset = base_queryset.filter(tags__id=tag_id)
        
        return base_queryset
    
    def get_context_data(self, **kwargs):
        """Add filter options to context."""
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['tags'] = Tag.objects.all()
        return context


class PromptDetailView(DetailView):
    """Display detailed view of a single prompt."""
    
    model = Prompt
    template_name = 'prompts/prompt_detail.html'
    context_object_name = 'prompt'


class PromptCreateView(CreateView):
    """Handle creation of new prompts."""
    
    model = Prompt
    form_class = PromptForm
    template_name = 'prompts/prompt_form.html'
    success_url = reverse_lazy('prompt_list')
    
    def form_valid(self, form):
        """Process valid form and show success message."""
        messages.success(self.request, 'Промпт успешно создан!')
        return super().form_valid(form)


class PromptUpdateView(UpdateView):
    """Handle updates to existing prompts."""
    
    model = Prompt
    form_class = PromptForm
    template_name = 'prompts/prompt_form.html'
    
    def get_success_url(self):
        """Generate URL to redirect after successful update."""
        return reverse_lazy('prompt_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """Process valid form and show success message."""
        messages.success(self.request, 'Промпт успешно обновлен!')
        return super().form_valid(form)


class PromptDeleteView(DeleteView):
    """Handle prompt deletion with protection for default prompts."""
    
    model = Prompt
    template_name = 'prompts/prompt_confirm_delete.html'
    success_url = reverse_lazy('prompt_list')
    
    def get(self, request, *args, **kwargs):
        """Prevent deletion of default prompts."""
        prompt_to_delete = self.get_object()
        if prompt_to_delete.is_default:
            messages.error(
                request,
                'Невозможно удалить предустановленный промпт!'
            )
            return redirect('prompt_detail', pk=prompt_to_delete.pk)
        return super().get(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """Delete prompt and show confirmation message."""
        messages.success(request, 'Промпт успешно удален!')
        return super().delete(request, *args, **kwargs)


class ImportPromptsView(FormView):
    """Handle importing prompts from JSON file."""
    
    template_name = 'prompts/import_prompts.html'
    form_class = ImportPromptsForm
    success_url = reverse_lazy('prompt_list')
    
    def form_valid(self, form):
        """Process valid form and import prompts."""
        json_file = form.cleaned_data['json_file']
        
        try:
            # Read and parse JSON
            file_content = json_file.read().decode('utf-8')
            prompts_data = json.loads(file_content)
            
            imported_count = 0
            skipped_count = 0
            
            for item in prompts_data:
                try:
                    # Validate required fields
                    if 'title' not in item or 'content' not in item:
                        skipped_count += 1
                        continue
                    
                    # Create or get category
                    category_name = item.get('category', 'Без категории')
                    category, _ = Category.objects.get_or_create(
                        name=category_name,
                        defaults={
                            'description': f'Категория {category_name}',
                            'color': '#3498db'
                        }
                    )
                    
                    # Create prompt
                    prompt = Prompt.objects.create(
                        title=item['title'],
                        content=item['content'],
                        category=category
                    )
                    
                    # Add tags
                    if 'tags' in item and isinstance(item['tags'], list):
                        for tag_name in item['tags']:
                            tag, _ = Tag.objects.get_or_create(
                                name=tag_name,
                                defaults={'description': f'Тег {tag_name}'}
                            )
                            prompt.tags.add(tag)
                    
                    # Add AI models
                    if 'ai_models' in item and isinstance(item['ai_models'], list):
                        for model_name in item['ai_models']:
                            model, _ = AIModel.objects.get_or_create(
                                name=model_name,
                                defaults={'description': f'AI модель {model_name}'}
                            )
                            prompt.ai_models.add(model)
                    
                    imported_count += 1
                    
                except Exception as e:
                    skipped_count += 1
                    continue
            
            # Show result message
            if imported_count > 0:
                messages.success(
                    self.request,
                    f'Успешно импортировано промптов: {imported_count}'
                )
            if skipped_count > 0:
                messages.warning(
                    self.request,
                    f'Пропущено промптов: {skipped_count}'
                )
            
        except json.JSONDecodeError:
            messages.error(
                self.request,
                'Ошибка: неверный формат JSON файла'
            )
        except Exception as e:
            messages.error(
                self.request,
                f'Ошибка при импорте: {str(e)}'
            )
        
        return super().form_valid(form)