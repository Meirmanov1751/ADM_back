from rest_framework import viewsets, status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Prefetch

from .filters import RepairFilter
from .models import Repair, RepairTask, RepairDelayReason, RepairStartMedia, RepairCompletionMedia, TaskDelayReason, RepairTaskMedia
from .serializers import RepairSerializer, RepairTaskSerializer, TaskDelayReasonSerializer, RepairDelayReasonSerializer

class RepairViewSet(viewsets.ModelViewSet):
    serializer_class = RepairSerializer
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = RepairFilter  # Только этот параметр для фильтрации

    def get_queryset(self):
        delay_reason_prefetch = Prefetch(
            'repairdelayreason',
            queryset=RepairDelayReason.objects.prefetch_related('media'),
            to_attr='delay_reason_prefetched'
        )
        return Repair.objects.all().prefetch_related(
            'tasks',
            'start_media',
            'completion_media',
            delay_reason_prefetch
        )
    @action(detail=True, methods=['post'], url_path='add-delay-reason')
    def add_delay_reason(self, request, pk=None):
        repair = self.get_object()
        if repair.status != 'delayed':
            return Response({"detail": "Ремонт должен быть в статусе 'Задерживается'", "status": repair.status},
                            status=status.HTTP_400_BAD_REQUEST)
        if repair.delay_reason:
            return Response({"detail": "Причина задержки уже указана"}, status=status.HTTP_400_BAD_REQUEST)

        print("Полученные данные:", request.data)  # Отладка
        serializer = RepairDelayReasonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(repair=repair)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        print("Ошибки сериализатора:", serializer.errors)  # Отладка
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='complete')
    def complete(self, request, pk=None):
        repair = self.get_object()
        repair.status = 'completed'
        repair.save(update_fields=['status'])

        completion_files = request.FILES.getlist('completion_files')
        for file in completion_files:
            RepairCompletionMedia.objects.create(repair=repair, file=file)

        serializer = self.get_serializer(repair)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        repair = self.get_object()
        for field in ['name', 'description', 'status']:
            if field in request.data:
                setattr(repair, field, request.data[field])
        repair.save()

        start_files = request.FILES.getlist('start_files')
        completion_files = request.FILES.getlist('completion_files')
        for file in start_files:
            RepairStartMedia.objects.create(repair=repair, file=file)
        for file in completion_files:
            RepairCompletionMedia.objects.create(repair=repair, file=file)

        serializer = self.get_serializer(repair)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RepairTaskViewSet(viewsets.ModelViewSet):
    serializer_class = RepairTaskSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        delay_reason_prefetch = Prefetch(
            'taskdelayreason',
            queryset=TaskDelayReason.objects.prefetch_related('media'),
            to_attr='delay_reason_prefetched'
        )
        return RepairTask.objects.all().prefetch_related(
            'media',
            delay_reason_prefetch
        )

    @action(detail=True, methods=['post'], url_path='add-delay-reason')
    def add_delay_reason(self, request, pk=None):
        task = self.get_object()
        if TaskDelayReason.objects.filter(task=task).exists():
            return Response({"detail": "Delay reason already exists"}, status=status.HTTP_400_BAD_REQUEST)

        serializer = TaskDelayReasonSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(task=task)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'], url_path='complete')
    def complete(self, request, pk=None):
        task = self.get_object()
        task.status = 'completed'
        task.description = request.data.get('description', task.description)
        task.save(update_fields=['status', 'description'])

        media_files = request.FILES.getlist('media_files')
        for media in media_files:
            RepairTaskMedia.objects.create(task=task, image=media)

        serializer = self.get_serializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        task = self.get_object()
        for field in ['name', 'description', 'status']:
            if field in request.data:
                setattr(task, field, request.data[field])
        task.save()

        media_files = request.FILES.getlist('media_files')
        for media in media_files:
            RepairTaskMedia.objects.create(task=task, image=media)

        serializer = self.get_serializer(task)
        return Response(serializer.data, status=status.HTTP_200_OK)