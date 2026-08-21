from django.contrib import admin
from .models import Conversation, Participant, Message, ReportedConversation

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at')
    search_fields = ('id',)

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('conversation__id', 'user__username')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'content', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('id', 'sender__username', 'content')
    ordering = ('timestamp',)

@admin.register(ReportedConversation)
class ReportedConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporter', 'conversation', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('reporter__username', 'conversation__id', 'reason')
