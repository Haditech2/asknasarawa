from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analytics.services import record_event

from .models import ChatFeedback, ChatMessage, Conversation
from .serializers import ChatMessageInputSerializer, ChatMessageSerializer, FeedbackInputSerializer, FeedbackSerializer
from .services import clear_conversation, process_message
from .throttles import ChatMessageThrottle


@method_decorator(csrf_protect, name="dispatch")
class ChatMessageAPIView(APIView):
    permission_classes = (permissions.AllowAny,)
    throttle_classes = (ChatMessageThrottle,)

    def post(self, request):
        serializer = ChatMessageInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = process_message(
            request,
            serializer.validated_data["message"],
            preferred_language=serializer.validated_data["preferred_language"],
            category=serializer.validated_data.get("category") or None,
        )
        return Response(result, status=status.HTTP_200_OK)


@method_decorator(ensure_csrf_cookie, name="dispatch")
class ChatHistoryAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        get_token(request)
        conversation_id = request.session.get("chat_conversation_id")
        session_key = request.session.session_key
        if not conversation_id or not session_key:
            return Response({"conversation_id": None, "messages": []})
        conversation = Conversation.objects.filter(
            pk=conversation_id,
            session_id=session_key,
            is_active=True,
        ).first()
        if not conversation:
            return Response({"conversation_id": None, "messages": []})
        messages = conversation.messages.select_related("matched_faq").order_by("created_at")[:100]
        return Response(
            {
                "conversation_id": conversation.pk,
                "preferred_language": conversation.preferred_language,
                "messages": ChatMessageSerializer(messages, many=True).data,
            }
        )


@method_decorator(csrf_protect, name="dispatch")
class ChatFeedbackAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = FeedbackInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session_key = request.session.session_key
        message = ChatMessage.objects.filter(
            pk=serializer.validated_data["message_id"],
            sender=ChatMessage.Sender.BOT,
            conversation__session_id=session_key,
        ).first()
        if not message:
            return Response({"error": "Message not found in this session."}, status=404)
        feedback, _ = ChatFeedback.objects.update_or_create(
            message=message,
            defaults={
                "helpful": serializer.validated_data["helpful"],
                "comment": serializer.validated_data.get("comment", ""),
            },
        )
        record_event(
            "feedback",
            language=message.language,
            metadata={"message_id": message.pk, "helpful": feedback.helpful},
        )
        return Response(FeedbackSerializer(feedback).data)


@method_decorator(csrf_protect, name="dispatch")
class ChatClearAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        clear_conversation(request)
        return Response({"cleared": True})
