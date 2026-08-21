from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('inbox/', views.ChatInboxView.as_view(), name='chat_inbox'),
    path('thread/<uuid:partner_id>/', views.ChatThreadView.as_view(), name='chat_thread'),
    path('block/<uuid:partner_id>/', views.ChatBlockUserView.as_view(), name='chat_block'),
    path('report/<uuid:conversation_id>/', views.ChatReportConversationView.as_view(), name='chat_report'),
    
    # API endpoints for AJAX polling
    path('api/messages/<uuid:partner_id>/', views.ChatApiMessagesView.as_view(), name='api_messages'),
    path('api/typing/<uuid:partner_id>/', views.ChatTypingStatusView.as_view(), name='api_typing'),
]
