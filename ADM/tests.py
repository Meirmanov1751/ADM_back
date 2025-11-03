import random
from django.test import TestCase
from django.utils import timezone
from user.models import User
from .models import Request, ASCCover, ASCFiles, RequestHistory, RequestRating


class TestDataGenerationTestCase(TestCase):
    def setUp(self):
        # Создание пользователей
        self.users = [User.objects.create_user(username=f'testuser{i}', password='1234') for i in range(5)]

    def test_generate_requests_with_related_data(self):
        for i in range(20):
            req = Request.objects.create(
                user=random.choice(self.users),
                signatory=random.choice(self.users),
                moderator=random.choice(self.users),
                executor=random.choice(self.users),
                category='aho',
                type=random.choice([c[0] for c in Request._meta.get_field('type').choices]),
                description=f'Описание запроса {i}',
                region='Алматы',
                city='Алматы',
                status=random.choice([s[0] for s in Request._meta.get_field('status').choices])
            )

            # Обложки
            for j in range(random.randint(1, 3)):
                ASCCover.objects.create(
                    ASC=req,
                    alt=f'Обложка {j} для заявки {req.id}',
                    order=j
                )

            # Файлы
            for j in range(random.randint(1, 2)):
                ASCFiles.objects.create(
                    ASC=req,
                    title=f'Файл {j} для заявки {req.id}'
                )

            # История
            for j in range(random.randint(1, 4)):
                RequestHistory.objects.create(
                    request=req,
                    user=random.choice(self.users),
                    action=random.choice(['Создание', 'Обновление', 'Изменение статуса']),
                    details=f'Детали действия {j}'
                )

            # Рейтинг
            if random.choice([True, False]):
                RequestRating.objects.create(
                    request=req,
                    user=random.choice(self.users),
                    rating=random.randint(1, 5),
                    comment=f'Комментарий к заявке {req.id}'
                )

        self.assertEqual(Request.objects.count(), 20)
        self.assertTrue(RequestHistory.objects.exists())
        self.assertTrue(ASCFiles.objects.exists())
        self.assertTrue(ASCCover.objects.exists())
