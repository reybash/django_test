from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework import permissions

from courses.models import Course


class CustomUser(AbstractUser):
    """Кастомная модель пользователя - студента."""

    email = models.EmailField(
        verbose_name='Адрес электронной почты',
        max_length=250,
        unique=True
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = (
        'username',
        'first_name',
        'last_name',
        'password'
    )

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('-id',)

    def __str__(self):
        return self.get_full_name()


class Balance(models.Model):
    """Модель баланса пользователя."""

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='balance',
        verbose_name='Пользователь'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Баланс',
        default=1000.00
    )

    objects = models.Manager()

    class Meta:
        verbose_name = 'Баланс'
        verbose_name_plural = 'Балансы'
        ordering = ('-id',)

    def __str__(self):
        return f"Баланс {self.user}: {self.amount} бонусов"

    def save(self, *args, **kwargs):
        if self.amount < 0:
            raise ValueError("Баланс пользователя не может быть ниже 0.")
        super().save(*args, **kwargs)


# Автоматическое создание баланса при создании пользователя
@receiver(post_save, sender=CustomUser)
def create_user_balance(sender, instance, created, **kwargs):
    if created:
        Balance.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_balance(sender, instance, **kwargs):
    if hasattr(instance, 'balance'):
        instance.balance.save()


# Ограничение изменения баланса через REST-API
class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Разрешение, позволяющее только пользователям с правами is_staff изменять данные.
    """

    def has_permission(self, request, view):
        if view.action in ['update', 'partial_update']:
            return request.user.is_staff
        return True


class Subscription(models.Model):
    """Модель подписки пользователя на курс."""

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='course_accesses',
        verbose_name='Пользователь',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='user_accesses',
        verbose_name='Курс',
    )
    granted_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата и время предоставления доступа',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ('-id',)

    def __str__(self):
        return f"{self.user} - {self.course}"
