"""
Views for Prompt Manager application.
"""
import json
import re

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
from django.shortcuts import redirect, get_object_or_404, render
from django.http import JsonResponse

from .models import Prompt, Category, Tag, AIModel, Collection, PromptVariable
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

        # Filter by multiple categories (fix for empty strings)
        category_ids = [
            cat_id for cat_id in self.request.GET.getlist('category')
            if cat_id and cat_id.strip()
        ]
        if category_ids:
            base_queryset = base_queryset.filter(category_id__in=category_ids)

        # Filter by multiple tags (fix for empty strings)
        tag_ids = [
            tag_id for tag_id in self.request.GET.getlist('tag')
            if tag_id and tag_id.strip()
        ]
        if tag_ids:
            # Prompts must have ALL selected tags
            for tag_id in tag_ids:
                base_queryset = base_queryset.filter(tags__id=tag_id)

        # Filter by collection
        collection_id = self.request.GET.get('collection', '').strip()
        if collection_id:
            base_queryset = base_queryset.filter(collection_id=collection_id)

        # Filter favorites
        show_favorites = self.request.GET.get('favorites')
        if show_favorites:
            base_queryset = base_queryset.filter(is_favorite=True)

        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        allowed_sorts = [
            '-created_at', 'created_at',
            '-usage_count', 'usage_count', 'title'
        ]
        if sort_by in allowed_sorts:
            base_queryset = base_queryset.order_by(sort_by)

        return base_queryset.distinct()

    def get_context_data(self, **kwargs):
        """Add filter options to context."""
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['tags'] = Tag.objects.all()
        context['collections'] = Collection.objects.all()
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        context['selected_categories'] = self.request.GET.getlist('category')
        context['selected_tags'] = self.request.GET.getlist('tag')
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
        collection_name = form.cleaned_data.get('collection_name', '').strip()

        # Create or get collection if specified
        collection = None
        if collection_name:
            collection, _ = Collection.objects.get_or_create(
                name=collection_name,
                defaults={
                    'description': f'Импортированная коллекция: {collection_name}',
                    'color': '#9b59b6'
                }
            )

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

                    # Use collection from form or from JSON
                    item_collection = collection
                    if 'collection' in item and not collection_name:
                        item_collection, _ = Collection.objects.get_or_create(
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
                        collection=item_collection
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

                except Exception:
                    skipped_count += 1

            # Show result message
            if imported_count > 0:
                msg = f'Успешно импортировано промптов: {imported_count}'
                if collection_name:
                    msg += f' в коллекцию "{collection_name}"'
                messages.success(self.request, msg)
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
        except Exception as error:
            messages.error(
                self.request,
                f'Ошибка при импорте: {str(error)}'
            )

        return super().form_valid(form)


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
                processed_content = processed_content.replace(
                    placeholder, value.strip()
                )

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
            avg_usage = (
                total_usage / prompts_in_category.count()
                if prompts_in_category.count() > 0 else 0
            )
            category_stats.append({
                'category': category,
                'count': prompts_in_category.count(),
                'total_usage': total_usage,
                'avg_usage': avg_usage
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
        context['favorites_count'] = Prompt.objects.filter(
            is_favorite=True
        ).count()

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
        except Exception as error:
            return JsonResponse({
                'success': False,
                'error': str(error)
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
        except Exception as error:
            return JsonResponse({
                'success': False,
                'error': str(error)
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
        except Exception as error:
            return JsonResponse({
                'success': False,
                'error': str(error)
            }, status=400)


class AddToCollectionView(View):
    """AJAX endpoint to add prompt to collection."""

    def post(self, request, pk):
        """Add prompt to collection."""
        try:
            prompt = get_object_or_404(Prompt, pk=pk)
            data = json.loads(request.body)
            collection_id = data.get('collection_id')

            if collection_id:
                collection = get_object_or_404(Collection, pk=collection_id)
                prompt.collection = collection
                prompt.save(update_fields=['collection'])
                return JsonResponse({
                    'success': True,
                    'collection_name': collection.name,
                    'collection_color': collection.color
                })

            # Remove from collection
            prompt.collection = None
            prompt.save(update_fields=['collection'])
            return JsonResponse({
                'success': True,
                'collection_name': None
            })

        except Exception as error:
            return JsonResponse({
                'success': False,
                'error': str(error)
            }, status=400)