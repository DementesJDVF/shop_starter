from django.urls import path

from apps.ai.views.search_views import AISearchView

urlpatterns = [
    path("search/", AISearchView.as_view(), name="ai-search"),
]
