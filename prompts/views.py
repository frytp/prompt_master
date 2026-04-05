from django.views.generic import (
    ListView, 
    DetailView, 
    CreateView, 
    UpdateView, 
    DeleteView,
    FormView,
    View,
    TemplateView
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
import json
import re
from .models import Prompt, Category, Tag, AIModel, Collection
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
            'category', 'collection'
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
        
        # Filter by collection
        collection_id = self.request.GET.get('collection')
        if collection_id:
            base_queryset = base_queryset.filter(collection_id=collection_id)
        
        # Filter favorites
        show_favorites = self.request.GET.get('favorites')
        if show_favorites:
            base_queryset = base_queryset.filter(is_favorite=True)
        
        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        if sort_by in ['-created_at', 'created_at', '-usage_count', 'usage_count', 'title']:
            base_queryset = base_queryset.order_by(sort_by)
        
        return base_queryset
    
    def get_context_data(self, **kwargs):
        """Add filter options to context."""
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['tags'] = Tag.objects.all()
        context['collections'] = Collection.objects.all()
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
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
                    
                    # Create or get collection if specified
                    collection = None
                    if 'collection' in item:
                        collection, _ = Collection.objects.get_or_create(
                            name=item['collection'],
                            defaults={
                                'description': f'Коллекция {item["collection"]}',
                                'color': '#9b59b6'
                            }
                        )
                    
                    # Create prompt
                    prompt = Prompt.objects.create(
                        title=item['title'],
                        content=item['content'],
                        category=category,
                        collection=collection
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


class IncrementUsageView(View):
    """AJAX endpoint to increment prompt usage counter."""
    
    def post(self, request, pk):
        """Increment usage count for prompt."""
        try:
            prompt = get_object_or_404(Prompt, pk=pk)
            prompt.increment_usage()
            return JsonResponse({
                'success': True,
                'usage_count': prompt.usage_count
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class GetPromptContentView(View):
    """AJAX endpoint to get prompt content."""
    
    def get(self, request, pk):
        """Get prompt content."""
        try:
            prompt = get_object_or_404(Prompt, pk=pk)
            return JsonResponse({
                'success': True,
                'content': prompt.content,
                'title': prompt.title
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class ToggleFavoriteView(View):
    """AJAX endpoint to toggle favorite status."""
    
    def post(self, request, pk):
        """Toggle favorite status."""
        try:
            prompt = get_object_or_404(Prompt, pk=pk)
            prompt.is_favorite = not prompt.is_favorite
            prompt.save(update_fields=['is_favorite'])
            return JsonResponse({
                'success': True,
                'is_favorite': prompt.is_favorite
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
class ProcessPromptVariablesView(View):
    """Handle prompt variable substitution with history."""
    
    def get(self, request, pk):
        """Display form for variable substitution."""
        prompt = get_object_or_404(Prompt, pk=pk)
        
        # Extract variables from prompt content
        variables = re.findall(r'\{\{(\w+)\}\}', prompt.content)
        unique_variables = list(set(variables))
        
        # Get previous values for each variable
        previous_values = {}
        for var_name in unique_variables:
            recent_uses = PromptVariable.objects.filter(
                prompt=prompt,
                variable_name=var_name
            ).order_by('-used_at')[:5]
            previous_values[var_name] = [pv.value for pv in recent_uses]
        
        context = {
            'prompt': prompt,
            'variables': unique_variables,
            'previous_values': previous_values
        }
        
        return render(request, 'prompts/process_variables.html', context)
    
    def post(self, request, pk):
        """Process variable substitution and save to history."""
        prompt = get_object_or_404(Prompt, pk=pk)
        
        # Get variable values from POST data
        processed_content = prompt.content
        variables_used = []
        
        for key, value in request.POST.items():
            if key.startswith('var_') and value.strip():
                var_name = key[4:]  # Remove 'var_' prefix
                placeholder = f'{{{{{var_name}}}}}'
                processed_content = processed_content.replace(placeholder, value.strip())
                
                # Save to history
                PromptVariable.objects.create(
                    prompt=prompt,
                    variable_name=var_name,
                    value=value.strip()
                )
                variables_used.append(var_name)
        
        # Return JSON response for AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'processed_content': processed_content
            })
        
        # Or render template
        context = {
            'prompt': prompt,
            'processed_content': processed_content,
            'variables_used': variables_used
        }
        return render(request, 'prompts/processed_result.html', context)


class PromptStatisticsView(TemplateView):
    """Display statistics about prompt usage."""
    
    template_name = 'prompts/statistics.html'
    
    def get_context_data(self, **kwargs):
        """Add statistics to context."""
        context = super().get_context_data(**kwargs)
        
        # Total prompts
        context['total_prompts'] = Prompt.objects.count()
        
        # Most used prompts
        context['most_used'] = Prompt.objects.order_by('-usage_count')[:10]
        
        # Category statistics
        category_stats = []
        for category in Category.objects.all():
            prompts_in_category = category.prompts.all()
            total_usage = sum(p.usage_count for p in prompts_in_category)
            category_stats.append({
                'category': category,
                'count': prompts_in_category.count(),
                'total_usage': total_usage,
                'avg_usage': total_usage / prompts_in_category.count() if prompts_in_category.count() > 0 else 0
            })
        
        # Sort by total usage
        category_stats.sort(key=lambda x: x['total_usage'], reverse=True)
        context['category_stats'] = category_stats
        
        # Tag statistics
        tag_stats = []
        for tag in Tag.objects.all():
            prompts_with_tag = tag.prompts.all()
            total_usage = sum(p.usage_count for p in prompts_with_tag)
            tag_stats.append({
                'tag': tag,
                'count': prompts_with_tag.count(),
                'total_usage': total_usage
            })
        
        tag_stats.sort(key=lambda x: x['total_usage'], reverse=True)
        context['tag_stats'] = tag_stats[:10]
        
        # AI Model statistics
        model_stats = []
        for model in AIModel.objects.all():
            prompts_for_model = model.prompts.all()
            total_usage = sum(p.usage_count for p in prompts_for_model)
            model_stats.append({
                'model': model,
                'count': prompts_for_model.count(),
                'total_usage': total_usage
            })
        
        model_stats.sort(key=lambda x: x['total_usage'], reverse=True)
        context['model_stats'] = model_stats
        
        # Favorites count
        context['favorites_count'] = Prompt.objects.filter(is_favorite=True).count()
        
        # Collections statistics
        collection_stats = []
        for collection in Collection.objects.all():
            prompts_in_collection = collection.prompts.all()
            total_usage = sum(p.usage_count for p in prompts_in_collection)
            collection_stats.append({
                'collection': collection,
                'count': prompts_in_collection.count(),
                'total_usage': total_usage
            })
        
        collection_stats.sort(key=lambda x: x['total_usage'], reverse=True)
        context['collection_stats'] = collection_stats
        
        return context


class IncrementUsageView(View):
    """AJAX endpoint to increment prompt usage counter."""
    
    def post(self, request, pk):
        """Increment usage count for prompt."""
        try:
            prompt = get_object_or_404(Prompt, pk=pk)
            prompt.increment_usage()
            return JsonResponse({
                'success': True,
                'usage_count': prompt.usage_count
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class GetPromptContentView(View):
    """AJAX endpoint to get prompt content."""
    
    def get(self, request, pk):
        """Get prompt content."""
        try:
            prompt = get_object_or_404(Prompt, pk=pk)
            return JsonResponse({
                'success': True,
                'content': prompt.content,
                'title': prompt.title
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


class ToggleFavoriteView(View):
    """AJAX endpoint to toggle favorite status."""
    
    def post(self, request, pk):
        """Toggle favorite status."""
        try:
            prompt = get_object_or_404(Prompt, pk=pk)
            prompt.is_favorite = not prompt.is_favorite
            prompt.save(update_fields=['is_favorite'])
            return JsonResponse({
                'success': True,
                'is_favorite': prompt.is_favorite
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)