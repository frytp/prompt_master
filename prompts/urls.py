"""
URL patterns for prompts app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.PromptListView.as_view(), name='prompt_list'),
    path(
        'prompt/<int:pk>/',
        views.PromptDetailView.as_view(),
        name='prompt_detail'
    ),
    path(
        'prompt/<int:pk>/variables/',
        views.ProcessPromptVariablesView.as_view(),
        name='prompt_variables'
    ),
    path(
        'prompt/<int:pk>/increment/',
        views.IncrementUsageView.as_view(),
        name='prompt_increment'
    ),
    path(
        'prompt/<int:pk>/toggle-favorite/',
        views.ToggleFavoriteView.as_view(),
        name='prompt_toggle_favorite'
    ),
    path(
        'prompt/<int:pk>/add-to-collection/',
        views.AddToCollectionView.as_view(),
        name='prompt_add_to_collection'
    ),
    path(
        'prompt/create/',
        views.PromptCreateView.as_view(),
        name='prompt_create'
    ),
    path(
        'prompt/<int:pk>/update/',
        views.PromptUpdateView.as_view(),
        name='prompt_update'
    ),
    path(
        'prompt/<int:pk>/delete/',
        views.PromptDeleteView.as_view(),
        name='prompt_delete'
    ),
    path(
        'import/',
        views.ImportPromptsView.as_view(),
        name='prompt_import'
    ),
    path(
        'statistics/',
        views.PromptStatisticsView.as_view(),
        name='prompt_statistics'
    ),
    path(
        'api/prompt/<int:pk>/content/',
        views.GetPromptContentView.as_view(),
        name='api_prompt_content'
    ),
    path(
        'collections/create/',
        views.CollectionCreateView.as_view(),
        name='collection_create'),
]