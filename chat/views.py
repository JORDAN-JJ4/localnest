from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.contrib import messages

from .models import Message
from accounts.models import User
from notifications.models import Notification

class ChatInboxView(LoginRequiredMixin, View):
    """Inbox view displaying all users who have exchanged messages with the current user"""
    def get(self, request):
        user = request.user
        # Find all unique users who have chatted with the current user
        sent_to = Message.objects.filter(sender=user).values_list('receiver', flat=True)
        received_from = Message.objects.filter(receiver=user).values_list('sender', flat=True)
        
        chat_partner_ids = set(list(sent_to) + list(received_from))
        chat_partners = User.objects.filter(id__in=chat_partner_ids).exclude(id=user.id)

        return render(request, 'chat/inbox.html', {
            'chat_partners': chat_partners
        })


class ChatThreadView(LoginRequiredMixin, View):
    """Displays messages between current user and a target chat partner, and handles sending messages"""
    def get(self, request, partner_id):
        partner = get_object_or_404(User, id=partner_id)
        user = request.user
        
        # Mark all messages received from this partner as read
        Message.objects.filter(sender=partner, receiver=user, is_read=False).update(is_read=True)

        messages_list = Message.objects.filter(
            (Q(sender=user) & Q(receiver=partner)) |
            (Q(sender=partner) & Q(receiver=user))
        ).order_by('timestamp')

        return render(request, 'chat/thread.html', {
            'partner': partner,
            'messages_list': messages_list
        })

    def post(self, request, partner_id):
        partner = get_object_or_404(User, id=partner_id)
        content = request.POST.get('content', '').strip()

        if not content:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Message content cannot be empty'})
            return redirect('chat:chat_thread', partner_id=partner.id)

        message = Message.objects.create(
            sender=request.user,
            receiver=partner,
            content=content
        )

        # Trigger notification to receiver
        Notification.objects.create(
            user=partner,
            title="New Message",
            message=f"{request.user.get_full_name() or request.user.username} sent you a message.",
            notification_type=Notification.Types.MESSAGE
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message_id': str(message.id),
                'content': message.content,
                'sender': message.sender.username,
                'timestamp': message.timestamp.strftime('%I:%M %p')
            })

        return redirect('chat:chat_thread', partner_id=partner.id)


from django.core.cache import cache

class ChatApiMessagesView(LoginRequiredMixin, View):
    def get(self, request, partner_id):
        partner = get_object_or_404(User, id=partner_id)
        user = request.user
        
        # Mark incoming messages as read
        Message.objects.filter(sender=partner, receiver=user, is_read=False).update(is_read=True)
        
        # Fetch thread
        messages_list = Message.objects.filter(
            (Q(sender=user) & Q(receiver=partner)) |
            (Q(sender=partner) & Q(receiver=user))
        ).order_by('timestamp')
        
        data = [{
            'id': str(msg.id),
            'sender_id': str(msg.sender.id),
            'sender': msg.sender.username,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%I:%M %p'),
            'is_read': msg.is_read
        } for msg in messages_list]
        
        return JsonResponse({'status': 'success', 'messages': data})


class ChatTypingStatusView(LoginRequiredMixin, View):
    def get(self, request, partner_id):
        is_typing = cache.get(f"typing_{partner_id}_to_{request.user.id}", False)
        return JsonResponse({'is_typing': bool(is_typing)})

    def post(self, request, partner_id):
        cache.set(f"typing_{request.user.id}_to_{partner_id}", True, timeout=4)
        return JsonResponse({'status': 'success'})
