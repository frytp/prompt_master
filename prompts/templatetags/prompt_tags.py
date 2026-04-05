"""
Custom template tags for prompt management.
"""
from django import template
from urllib.parse import urlencode

register = template.Library()


@register.simple_tag(takes_context=True)
def url_with_params(context, **kwargs):
    """
    Generate URL with current query parameters plus new ones.
    
    Usage: {% url_with_params page=2 %}
    """
    query = context['request'].GET.copy()
    for key, value in kwargs.items():
        query[key] = value
    return '?' + urlencode(query)


@register.simple_tag(takes_context=True)
def pagination_url(context, page_num):
    """
    Generate pagination URL preserving filters.
    
    Args:
        context: Template context
        page_num: Page number to navigate to
        
    Returns:
        str: URL with pagination and filters
    """
    params = context['request'].GET.copy()
    params['page'] = page_num
    return '?' + urlencode(params)


@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary by key.
    
    Usage: {{ dict|get_item:key }}
    """
    return dictionary.get(key)