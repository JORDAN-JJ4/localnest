import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib import messages
from django.core.cache import cache

from .models import Conversation, Participant, Message, ReportedConversation
from accounts.models import User, Block
from bookings.models import Booking
from notifications.models import Notification

def can_initiate_chat(user1, user2):
    if user1.is_admin() or user2.is_admin():
        return True
    if user1.is_tourist() and user2.is_host():
        return True
    if user1.is_host() and user2.is_tourist():
        return True
    return False

def get_or_create_conversation(user1, user2):
    common_convs = Conversation.objects.filter(
        participants__user=user1
    ).filter(
        participants__user=user2
    ).distinct()

    if common_convs.exists():
        return common_convs.first()

    conversation = Conversation.objects.create()
    Participant.objects.create(conversation=conversation, user=user1)
    Participant.objects.create(conversation=conversation, user=user2)
    return conversation


class ChatInboxView(LoginRequiredMixin, View):
    """Inbox view displaying active traveler or host conversations"""
    def get(self, request):
        user = request.user
        # Find all conversations the user is participating in
        user_convs = Conversation.objects.filter(participants__user=user)
        
        conversations_data = []
        for conv in user_convs:
            partner_part = conv.participants.exclude(user=user).first()
            if not partner_part:
                continue
            partner = partner_part.user
            
            last_message = conv.messages.order_by('-timestamp').first()
            unread_count = conv.messages.filter(is_read=False).exclude(sender=user).count()
            
            # Booking Context
            if user.is_tourist():
                guest, host = user, partner
            else:
                guest, host = partner, user
                
            booking = Booking.objects.filter(
                guest=guest,
                property__host=host
            ).exclude(
                status__in=['CANCELLED', 'REJECTED']
            ).order_by('start_date').first()
            
            conversations_data.append({
                'conversation': conv,
                'partner': partner,
                'last_message': last_message,
                'unread_count': unread_count,
                'booking': booking,
                'is_blocked': Block.objects.filter(blocker=user, blocked_user=partner).exists() or Block.objects.filter(blocker=partner, blocked_user=user).exists()
            })
        
        # Sort conversations by last message timestamp
        conversations_data.sort(
            key=lambda x: x['last_message'].timestamp if x['last_message'] else x['conversation'].created_at,
            reverse=True
        )
        
        if user.is_host():
            # Host inbox categories
            unread = [c for c in conversations_data if c['unread_count'] > 0]
            recent = conversations_data
            
            upcoming = []
            past = []
            today = datetime.date.today()
            
            for c in conversations_data:
                if c['booking']:
                    if c['booking'].start_date >= today:
                        upcoming.append(c)
                    else:
                        past.append(c)
                        
            return render(request, 'chat/inbox.html', {
                'unread': unread,
                'recent': recent,
                'upcoming': upcoming,
                'past': past,
                'is_host': True
            })
        else:
            # Traveler inbox categories
            host_convs = []
            support_convs = []
            for c in conversations_data:
                if c['partner'].is_admin():
                    support_convs.append(c)
                else:
                    host_convs.append(c)
                    
            return render(request, 'chat/inbox.html', {
                'host_convs': host_convs,
                'support_convs': support_convs,
                'is_host': False
            })


class ChatThreadView(LoginRequiredMixin, View):
    """Displays thread between user and partner, and manages new messages"""
    def get(self, request, partner_id):
        partner = get_object_or_404(User, id=partner_id)
        user = request.user

        if not can_initiate_chat(user, partner):
            return HttpResponseForbidden("You are not authorized to start a conversation with this user type.")

        # Ensure conversation exists
        conversation = get_or_create_conversation(user, partner)

        # Enforce server-side participant permission check
        is_participant = conversation.participants.filter(user=user).exists()
        if not is_participant:
            return HttpResponseForbidden("Access Denied.")

        # Mark incoming messages as read
        conversation.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)

        messages_list = conversation.messages.all().order_by('timestamp')

        # Find booking context
        if user.is_tourist():
            guest, host = user, partner
        else:
            guest, host = partner, user

        booking = Booking.objects.filter(
            guest=guest,
            property__host=host
        ).exclude(
            status__in=['CANCELLED', 'REJECTED']
        ).order_by('start_date').first()

        # Check block status
        user_blocked_partner = Block.objects.filter(blocker=user, blocked_user=partner).exists()
        partner_blocked_user = Block.objects.filter(blocker=partner, blocked_user=user).exists()

        return render(request, 'chat/thread.html', {
            'conversation': conversation,
            'partner': partner,
            'messages_list': messages_list,
            'booking': booking,
            'user_blocked_partner': user_blocked_partner,
            'partner_blocked_user': partner_blocked_user
        })

    def post(self, request, partner_id):
        partner = get_object_or_404(User, id=partner_id)
        user = request.user

        if not can_initiate_chat(user, partner):
            return HttpResponseForbidden("Action Forbidden.")

        conversation = get_or_create_conversation(user, partner)

        # Enforce participant permission check
        if not conversation.participants.filter(user=user).exists():
            return HttpResponseForbidden("Access Denied.")

        # Check block status before sending
        if Block.objects.filter(blocker=user, blocked_user=partner).exists() or Block.objects.filter(blocker=partner, blocked_user=user).exists():
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'You cannot send messages to a blocked user.'})
            messages.error(request, "Conversation is blocked.")
            return redirect('chat:chat_thread', partner_id=partner.id)

        content = request.POST.get('content', '').strip()
        attachment = request.FILES.get('attachment')

        if not content and not attachment:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'message': 'Message cannot be empty.'})
            return redirect('chat:chat_thread', partner_id=partner.id)

        # Validate file attachment if provided
        if attachment:
            if attachment.size > 5 * 1024 * 1024:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': 'Photo size must be under 5MB.'})
                messages.error(request, "Photo size must be under 5MB.")
                return redirect('chat:chat_thread', partner_id=partner.id)
            
            ext = attachment.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'gif']:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'status': 'error', 'message': 'Only JPG, PNG, and GIF photos are allowed.'})
                messages.error(request, "Only JPG, PNG, and GIF photos are allowed.")
                return redirect('chat:chat_thread', partner_id=partner.id)

        message = Message.objects.create(
            conversation=conversation,
            sender=user,
            content=content,
            attachment=attachment
        )

        # Update updated_at of conversation
        conversation.save()

        # Trigger notification
        Notification.objects.create(
            user=partner,
            title="New Message",
            message=f"{user.get_full_name() or user.username} sent you a message about your stay.",
            notification_type=Notification.Types.MESSAGE
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            attachment_url = message.attachment.url if message.attachment else None
            return JsonResponse({
                'status': 'success',
                'message_id': str(message.id),
                'content': message.content,
                'sender': message.sender.username,
                'attachment_url': attachment_url,
                'timestamp': message.timestamp.strftime('%I:%M %p')
            })

        return redirect('chat:chat_thread', partner_id=partner.id)


class ChatApiMessagesView(LoginRequiredMixin, View):
    """API endpoint to fetch messages in thread"""
    def get(self, request, partner_id):
        partner = get_object_or_404(User, id=partner_id)
        user = request.user
        
        conversation = get_or_create_conversation(user, partner)
        
        # Enforce server-side check
        if not conversation.participants.filter(user=user).exists():
            return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

        # Mark incoming messages as read
        conversation.messages.filter(is_read=False).exclude(sender=user).update(is_read=True)
        
        messages_list = conversation.messages.all().order_by('timestamp')
        
        data = [{
            'id': str(msg.id),
            'sender_id': str(msg.sender.id),
            'sender': msg.sender.username,
            'content': msg.content,
            'attachment_url': msg.attachment.url if msg.attachment else None,
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


class ChatBlockUserView(LoginRequiredMixin, View):
    """Toggles blocking status between current user and partner"""
    def post(self, request, partner_id):
        partner = get_object_or_404(User, id=partner_id)
        block, created = Block.objects.get_or_create(blocker=request.user, blocked_user=partner)
        if not created:
            block.delete()
            messages.success(request, f"You have unblocked {partner.get_full_name() or partner.username}.")
        else:
            messages.success(request, f"You have blocked {partner.get_full_name() or partner.username}.")
        return redirect('chat:chat_thread', partner_id=partner.id)


class ChatReportConversationView(LoginRequiredMixin, View):
    """Submits report against a conversation thread"""
    def post(self, request, conversation_id):
        conversation = get_object_or_404(Conversation, id=conversation_id)
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, "Please provide a reason for reporting.")
            return redirect('chat:chat_inbox')
        ReportedConversation.objects.create(
            reporter=request.user,
            conversation=conversation,
            reason=reason
        )
        messages.success(request, "The conversation has been reported to administration. Thank you.")
        
        partner_part = conversation.participants.exclude(user=request.user).first()
        if partner_part:
            return redirect('chat:chat_thread', partner_id=partner_part.user.id)
        return redirect('chat:chat_inbox')
