from django.shortcuts import render

# Create your views here.
"""
Views for Prompt Manager application.
"""
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Prompt
from .forms import PromptForm
from django.shortcuts import redirect



class PromptListView(ListView):
    """Display paginated list of prompts with search and filters."""
    
    model = Prompt
    template_name = 'prompts/prompt_list.html'
    context_object_name = 'prompts'
    paginate_by = 12
    
    def get_queryset(self):
        """
        Get optimized queryset with search and filtering.
        
        Returns:
            QuerySet: Filtered and optimized prompt queryset
        """
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
    """Display detailed view of a prompt."""
    
    model = Prompt
    template_name = 'prompts/prompt_detail.html'
    context_object_name = 'prompt'
    
class PromptCreateView(CreateView):
    """Create new prompt."""
    
    model = Prompt
    form_class = PromptForm
    template_name = 'prompts/prompt_form.html'
    success_url = reverse_lazy('prompt_list')
    
    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, 'Промпт успешно создан!')
        return super().form_valid(form)
        
class PromptUpdateView(UpdateView):
    """Update existing prompt."""
    
    model = Prompt
    form_class = PromptForm
    template_name = 'prompts/prompt_form.html'
    
    def get_success_url(self):
        """Redirect to detail view after update."""
        return reverse_lazy('prompt_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """Handle successful form submission."""
        messages.success(self.request, 'Промпт успешно обновлен!')
        return super().form_valid(form)

class PromptDeleteView(DeleteView):
    """Delete prompt."""
    
    model = Prompt
    template_name = 'prompts/prompt_confirm_delete.html'
    success_url = reverse_lazy('prompt_list')
    
    def get(self, request, *args, **kwargs):
        """Check if prompt can be deleted."""
        self.object = self.get_object()
        if self.object.is_default:
            messages.error(
                request,
                'Невозможно удалить предустановленный промпт'
            )
            return redirect('prompt_detail', pk=self.object.pk)
        return super().get(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """Handle deletion."""
        messages.success(request, 'Промпт успешно удален')
        return super().delete(request, *args, **kwargs)