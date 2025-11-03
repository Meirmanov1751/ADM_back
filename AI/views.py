from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
import openai
import os
import PyPDF2

from .models import ChatMessage, KnowledgeBase
from .serializers import ChatMessageSerializer, KnowledgeBaseSerializer

# Получаем API-ключ из переменных окружения
openai.api_key = "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"


class KnowledgeBaseUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        serializer = KnowledgeBaseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def generate_ai_response(user_message, role):
    """Функция для генерации ответа на основе базы знаний и OpenAI"""

    if not openai.api_key:
        return Response({'error': 'API-ключ не найден'}, status=500)

    # Загружаем все документы нужной категории
    category = "law" if role == "юрист" else "accounting"
    docs = KnowledgeBase.objects.filter(category=category)

    knowledge_text = ""
    for doc in docs:
        with open(doc.file.path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                knowledge_text += page.extract_text() + "\n"

    # Создаем запрос к OpenAI с контекстом документов
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"Ты — AI-{role} от СЕРВИСНАЯ ФАБРИКА - ФИЛИАЛ АО КАЗАХТЕЛЕКОМ. Используй эту информацию:\n{knowledge_text}"},
            {"role": "user", "content": user_message}
        ]
    )

    return response["choices"][0]["message"]["content"]


class ChatBotLView(APIView):
    """AI-юрист"""

    def post(self, request):
        user_message = request.data.get('message')
        if not user_message:
            return Response({'error': 'Message is required'}, status=400)

        bot_response = generate_ai_response(user_message, "юрист")

        # Сохранение в БД
        chat_message = ChatMessage.objects.create(message=user_message, response=bot_response)

        return Response(ChatMessageSerializer(chat_message).data)


class ChatBotAView(APIView):
    """AI-бухгалтер"""

    def post(self, request):
        user_message = request.data.get('message')
        if not user_message:
            return Response({'error': 'Message is required'}, status=400)

        bot_response = generate_ai_response(user_message, "бухгалтер")

        # Сохранение в БД
        chat_message = ChatMessage.objects.create(message=user_message, response=bot_response)

        return Response(ChatMessageSerializer(chat_message).data)
