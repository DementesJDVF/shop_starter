from django.urls import path
from .views import ChatAssistantView, VendorAIHistoryView

urlpatterns = [
    path("assistant/", ChatAssistantView.as_view(), name="chat_assistant"),
    path("history/", VendorAIHistoryView.as_view(), name="chat_history"),
]
