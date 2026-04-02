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


class PromptListView(ListView):
    """Display list of all prompts."""
    
    model = Prompt
    template_name = 'prompts/prompt_list.html'
    context_object_name = 'prompts'
    paginate_by = 12
    
    def get_queryset(self):
        """Get queryset with optional filtering."""
        queryset = Prompt.objects.select_related('category').prefetch_related(
            'tags', 'ai_models'
        )
        
        # Search by title
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        # Filter by category
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by tag
        tag_id = self.request.GET.get('tag')
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        
        return queryset
class PromptDetailView(DetailView):
    """Display detailed view of a prompt."""
    
    model = Prompt
    template_name = 'prompts/prompt_detail.html'
    context_object_name = 'prompt'