from django.db import models, transaction
from django.db.models import Count
from django.utils import timezone
from .consts import DEFAULT_AMOUNT_GROUPS, MAX_GROUP_USERS


class Course(models.Model):
    """Модель продукта - курса."""

    author = models.CharField(
        max_length=250,
        verbose_name='Автор',
    )
    title = models.CharField(
        max_length=250,
        verbose_name='Название',
    )
    start_date = models.DateTimeField(
        auto_now=False,
        auto_now_add=False,
        verbose_name='Дата и время начала курса'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Стоимость',
    )

    @property
    def is_available(self):
        """Проверяет доступность курса для отображения."""
        return self.start_date <= timezone.now()

    class Meta:
        verbose_name = 'Курс'
        verbose_name_plural = 'Курсы'
        ordering = ('-id',)

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """Модель урока."""

    title = models.CharField(
        max_length=250,
        verbose_name='Название',
    )
    link = models.URLField(
        max_length=250,
        verbose_name='Ссылка',
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name='Курс',
    )

    class Meta:
        verbose_name = 'Урок'
        verbose_name_plural = 'Уроки'
        ordering = ('id',)

    def __str__(self):
        return self.title


class Group(models.Model):
    """Модель группы."""

    name = models.CharField(
        max_length=100,
        verbose_name='Название группы'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='groups',
        verbose_name='Курс'
    )
    students = models.ManyToManyField(
        'users.CustomUser',
        related_name='course_groups',
        verbose_name='Студенты'
    )

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'
        ordering = ('-id',)

    def __str__(self):
        return f"{self.name} ({self.course})"


def assign_user_to_group(user, course):
    """
    Назначает пользователя в группу для указанного курса.
    """
    # Проверяем, есть ли у пользователя уже группа для этого курса
    if Group.objects.filter(students=user, course=course).exists():
        return  # Если пользователь уже состоит в группе, выходим из функции

    # Получаем все группы, связанные с курсом, с подсчетом студентов
    groups = course.groups.annotate(num_students=Count('students')).order_by(
        'num_students')

    # Если нет групп, создаем 10 групп для этого курса
    if not groups.exists():
        with transaction.atomic():
            for i in range(DEFAULT_AMOUNT_GROUPS):
                Group.objects.create(name=f'Group {i + 1}', course=course)
        # Повторно получаем группы после их создания
        groups = course.groups.annotate(
            num_students=Count('students')).order_by('num_students')

    # Ищем первую группу с менее 30 студентами
    group = groups.filter(num_students__lt=MAX_GROUP_USERS).first()

    if group is None:
        # Если все существующие группы полны, создаем новую группу
        with transaction.atomic():
            group = Group.objects.create(
                name=f'Group {course.groups.count() + 1}', course=course)

    # Добавляем пользователя в выбранную группу
    group.students.add(user)
