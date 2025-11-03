from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import serializers
from .models import Request, RequestHistory, RequestRating, User, City, RequestCategory, Region, UserGroup
from .serializers import RequestSerializer, RequestRatingSerializer, CitySerializer, RequestCategory, \
    RequestCategorySerializer, RegionSerializer, RequestInfoSerializer
from .camunda import start_request_process, complete_latest_task_by_request
import logging
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger(__name__)

class StandardPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class RequestInfoViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Request.objects.all()
    serializer_class = RequestInfoSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        group_ids = self.request.query_params.get('group_ids')
        status = self.request.query_params.get('status')
        signatory_id = self.request.query_params.get('signatory_id')
        executor_id = self.request.query_params.get('executor_id')

        logger.debug(
            f"Query params: group_ids={group_ids}, status={status}, signatory_id={signatory_id}, executor_id={executor_id}")

        if group_ids:
            group_ids = group_ids.split(',')
            queryset = queryset.filter(moderator_group__id__in=group_ids)

        if status:
            statuses = status.split(',')
            queryset = queryset.filter(status__in=statuses)

        if signatory_id:
            queryset = queryset.filter(signatory_id=signatory_id)

        if executor_id:
            queryset = queryset.filter(executor_id=executor_id)

        logger.debug(f"Filtered queryset: {queryset.count()} items")
        return queryset.distinct()

class RequestViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                     mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Request.objects.all()
    serializer_class = RequestSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        group_ids = self.request.query_params.get('group_ids')
        status = self.request.query_params.get('status')
        signatory_id = self.request.query_params.get('signatory_id')
        executor_id = self.request.query_params.get('executor_id')

        logger.debug(
            f"Query params: group_ids={group_ids}, status={status}, signatory_id={signatory_id}, executor_id={executor_id}")

        if group_ids:
            group_ids = group_ids.split(',')
            queryset = queryset.filter(moderator_group__id__in=group_ids)

        if status:
            statuses = status.split(',')
            queryset = queryset.filter(status__in=statuses)

        if signatory_id:
            queryset = queryset.filter(signatory_id=signatory_id)

        if executor_id:
            queryset = queryset.filter(executor_id=executor_id)

        logger.debug(f"Filtered queryset: {queryset.count()} items")
        return queryset.distinct()

    def create(self, request, *args, **kwargs):
        logger.debug(f"Received raw data: {request.data}")
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            logger.error(f"Validation error: {str(e.detail)}")
            return Response({"error": str(e.detail)}, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        request_obj = serializer.instance

        # Assign moderator group automatically based on category, region, city
        category = request_obj.category
        region = request_obj.region
        city = request_obj.city
        moderator_group = UserGroup.objects.filter(
            categories=category,
            regions=region,
            cities=city
        ).first()
        if moderator_group:
            request_obj.moderator_group = moderator_group
            request_obj.save()

        request_id = request_obj.id
        comment = request.data.get('comment', '')
        user_id = request.data.get('user_id')
        signatory_id = request.data.get('signatory_id')
        if not user_id or not signatory_id:
            return Response({"error": "user_id и signatory_id обязательны"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(pk=user_id)
            signatory = User.objects.get(pk=signatory_id)
        except User.DoesNotExist:
            return Response({"error": "Пользователь или подписант не найден"}, status=status.HTTP_400_BAD_REQUEST)
        start_request_process(request_id)
        RequestHistory.objects.create(
            request=request_obj,
            user=user,
            action='created',
            details=comment,
            user_full_name=f"{user.first_name} {user.last_name}",
            related_user_full_name=f"{signatory.first_name} {signatory.last_name}"
        )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'], url_path='count_for_signatory')
    def count_for_signatory(self, request, *args, **kwargs):
        """
        Возвращает количество заявок, ожидающих подписи конкретного подписанта.
        Пример: /api/requests/count_for_signatory/?signatory_id=12
        """
        signatory_id = request.query_params.get('signatory_id')

        if not signatory_id:
            return Response({'error': 'signatory_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            signatory = User.objects.get(id=signatory_id)
        except User.DoesNotExist:
            return Response({'error': 'Подписант не найден'}, status=status.HTTP_404_NOT_FOUND)

        # Считаем заявки, ожидающие подписи
        count = Request.objects.filter(
            signatory_id=signatory.id,
            status='pending'
        ).count()

        return Response({'signatory_id': signatory.id, 'pending_requests_count': count})

    @action(detail=False, methods=['get'], url_path='pending')
    def pending_requests(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id', 1)  # Default to 1
        queryset = self.get_queryset().filter(status='pending', user_id=user_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit_request(self, request, pk=None):
        request_obj = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_400_BAD_REQUEST)
        request_obj.status = 'pending'
        request_obj.save()
        complete_latest_task_by_request(request_obj.id, 'submitted')
        RequestHistory.objects.create(request=request_obj, user=user, action='submitted')
        return Response({'status': 'submitted'})

    @action(detail=True, methods=['post'], url_path='sign')
    def signatory_sign(self, request, pk=None):
        request_obj = self.get_object()
        user_id = request.data.get('user_id')
        comment = request.data.get('comment', '')

        if not user_id:
            return Response({'error': 'Нужен user_id'}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=400)

        if request_obj.status != 'pending':
            return Response({'error': 'Неверный статус'}, status=400)

        # 🔍 Поиск группы по региону, городу и категории
        matching_groups = UserGroup.objects.filter(
            regions=request_obj.region,
            cities=request_obj.city,
            categories=request_obj.category
        ).distinct()

        if not matching_groups.exists():
            return Response({'error': 'Группа модераторов не найдена по региону, городу и категории'}, status=404)

        moderator_group = matching_groups.first()  # можно доработать приоритет выбора

        request_obj.status = 'signed'
        request_obj.moderator_group = moderator_group
        request_obj.save()

        complete_latest_task_by_request(request_obj.id, 'signed')
        RequestHistory.objects.create(request=request_obj, user=user, action='signed', comment=comment)

        return Response({'status': 'signed'})

    @action(detail=False, methods=['get'], url_path='under_review')
    def under_review_requests(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id', 1)

    @action(detail=True, methods=['post'], url_path='moderator/review')
    def review_request(self, request, pk=None):
        request_obj = self.get_object()
        user_id = request.data.get('user_id')
        executor_id = request.data.get('executor_id')
        if not user_id or not executor_id:
            return Response({'error': 'user_id и executor_id обязательны'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=user_id)
            executor = User.objects.get(id=executor_id)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_400_BAD_REQUEST)
        if request_obj.status != 'signed':
            return Response({'error': 'Заявка еще не подписана'}, status=status.HTTP_400_BAD_REQUEST)
        request_obj.status = 'approved'
        request_obj.executor = executor
        request_obj.save()
        complete_latest_task_by_request(request_obj.id, 'approved')
        RequestHistory.objects.create(request=request_obj, user=user, action='reviewed')
        return Response({'status': 'approved'})

    @action(detail=True, methods=['post'], url_path='executor/start')
    def start_work(self, request, pk=None):
        request_obj = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_400_BAD_REQUEST)
        if request_obj.status != 'approved':
            return Response({'error': 'Заявка не одобрена'}, status=status.HTTP_400_BAD_REQUEST)
        request_obj.status = 'in_progress'
        request_obj.save()
        complete_latest_task_by_request(request_obj.id, 'in_progress')
        RequestHistory.objects.create(request=request_obj, user=user, action='started')
        return Response({'status': 'in_progress'})

    @action(detail=False, methods=['get'], url_path='for_executor')
    def executor_requests(self, request, *args, **kwargs):
        user_id = request.query_params.get('user_id', 1)  # Default to 1
        queryset = self.get_queryset().filter(
            status__in=['approved', 'in_progress'],
            executor_id=user_id
        )
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='executor/complete')
    def complete_request(self, request, pk=None):
        request_obj = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_400_BAD_REQUEST)
        if request_obj.status != 'in_progress':
            return Response({'error': 'Заявка не в работе'}, status=status.HTTP_400_BAD_REQUEST)
        request_obj.status = 'completed'
        request_obj.save()
        complete_latest_task_by_request(request_obj.id, 'completed')
        RequestHistory.objects.create(request=request_obj, user=user, action='completed')
        return Response({'status': 'completed'})

    @action(detail=True, methods=['post'], url_path='reject')
    def reject_request(self, request, pk=None):
        request_obj = self.get_object()
        user_id = request.data.get('user_id')
        comment = request.data.get('comment', '')
        if not user_id:
            return Response({'error': 'user_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_400_BAD_REQUEST)
        if request_obj.status != 'pending':
            return Response({'error': 'Неверный статус'}, status=status.HTTP_400_BAD_REQUEST)
        request_obj.status = 'rejected'
        request_obj.save()
        RequestHistory.objects.create(request=request_obj, user=user, action='rejected', comment=comment)
        return Response({'status': 'rejected'})

    @action(detail=True, methods=['post'], url_path='rate')
    def rate_request(self, request, pk=None):
        request_obj = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_400_BAD_REQUEST)
        if request_obj.status != 'completed':
            return Response({'error': 'Заявка не завершена'}, status=status.HTTP_400_BAD_REQUEST)
        if request_obj.user != user:
            return Response({'error': 'Вы не создатель заявки'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = RequestRatingSerializer(data=request.data)
        if serializer.is_valid():
            RequestRating.objects.update_or_create(
                request=request_obj,
                defaults={
                    'user': user,
                    'rating': serializer.validated_data['rating'],
                    'comment': serializer.validated_data.get('comment')
                }
            )
            request_obj.status = 'rated'
            request_obj.save()
            complete_latest_task_by_request(request_obj.id, 'rated')
            RequestHistory.objects.create(
                request=request_obj,
                user=user,
                action='rated',
                details=f"Оценка: {serializer.validated_data['rating']}"
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='reject_by_customer')
    def reject_by_customer(self, request, pk=None):
        request_obj = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id обязателен'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_400_BAD_REQUEST)
        if request_obj.status != 'completed':
            return Response({'error': 'Можно отправить на доработку только после завершения'}, status=status.HTTP_400_BAD_REQUEST)
        request_obj.status = 'in_progress'
        request_obj.save()
        complete_latest_task_by_request(request_obj.id, 'rejected_by_customer')
        RequestHistory.objects.create(request=request_obj, user=user, action='rejected_by_customer', details='Отправлено на доработку')
        return Response({'status': 'rejected_by_customer'})


class CityViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer

class RegionViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

class CategoryViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin,
                      mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    queryset = RequestCategory.objects.all()
    serializer_class = RequestCategorySerializer