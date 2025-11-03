from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils.translation import gettext as _
import logging

logger = logging.getLogger(__name__)


# User Manager
class UserManager(BaseUserManager):
    def create_superuser(self, email, password, **other_fields):
        other_fields.setdefault('is_staff', True)
        other_fields.setdefault('is_superuser', True)
        other_fields.setdefault('is_active', True)

        if other_fields.get('is_staff') is not True:
            raise ValueError('Superuser must be is_staff=True.')
        if other_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must be is_superuser=True.')

        return self.create_user(email, password, **other_fields)

    def create_user(self, email, password, **other_fields):
        if not email:
            raise ValueError(_('You must provide an email address'))

        email = self.normalize_email(email)
        other_fields.setdefault('is_active', True)
        other_fields.setdefault('is_staff', True)

        user = self.model(email=email, **other_fields)
        user.set_password(password)
        user.save()
        return user


# Organization Model
class Organization(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name or self.id

    class Meta:
        verbose_name = 'Организация'
        verbose_name_plural = 'Организации'


# Department Model
class Department(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    parent_id = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE,
                                  related_name='sub_departments')

    def __str__(self):
        return self.name or self.id

    class Meta:
        verbose_name = 'Департамент'
        verbose_name_plural = 'Департаменты'


# Position Model
class Position(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Должность'
        verbose_name_plural = 'Должности'


# Status Model
class Status(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name or self.id

    class Meta:
        verbose_name = 'Статус'
        verbose_name_plural = 'Статусы'


# Extended User Model
class User(AbstractBaseUser):
    class ROLES:
        GUEST = 'guest'
        MODERATOR = 'moderator'
        EXECUTOR = 'executor'
        SUPER_ADMIN = 'super_admin'

        ROLES_CHOICES = (
            (SUPER_ADMIN, 'Супер әкімші'),
            (GUEST, 'Гость'),
            (MODERATOR, 'Модератор'),
            (EXECUTOR, 'исполнитель'),
        )

    avatar = models.ImageField(upload_to='avatars/%Y', blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, default='')
    last_name = models.CharField(max_length=100, blank=True, default='')
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    confirmation_code = models.CharField(max_length=6, blank=True, null=True)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLES.ROLES_CHOICES, default=ROLES.GUEST)

    # Additional fields from EmployeeMaxInfo
    login = models.CharField(max_length=100, blank=True, default='', db_index=True)
    iin = models.CharField(max_length=12, blank=True, null=True)  # Assuming IIN is a 12-digit identifier
    personnel_number = models.CharField(max_length=50, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    is_mol = models.BooleanField(default=False)  # Materially responsible person
    server = models.CharField(max_length=100, blank=True, null=True)

    # Foreign keys to related models
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.ForeignKey(Status, on_delete=models.SET_NULL, null=True, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['role', 'first_name', 'last_name', 'phone_number']

    objects = UserManager()

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email}) - {self.role}'

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_super_admin(self):
        return self.role == self.ROLES.SUPER_ADMIN

    @property
    def is_journalists(self):
        return self.role == self.ROLES.JOURNALIST

    @property
    def is_guest(self):
        return self.role == self.ROLES.GUEST

    def get_group_requests(self):
        from ADM.models import Request
        region_ids = self.groups.values_list('regions__id', flat=True)
        city_ids = self.groups.values_list('cities__id', flat=True)
        category_ids = self.groups.values_list('categories__id', flat=True)

        return Request.objects.filter(
            models.Q(region__id__in=region_ids) |
            models.Q(city__id__in=city_ids) |
            models.Q(category__id__in=category_ids)
        ).distinct()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'