from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User  # Стандартный пользователь


# class CustomUser(AbstractUser):
#     """Кастомная модель пользователя"""
#     email = models.EmailField(unique=True, verbose_name='Email')
#     created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата регистрации')
#
#     def __str__(self):
#         return self.username
#
#     class Meta:
#         db_table = 'custom_user'
#         verbose_name = 'Пользователь'
#         verbose_name_plural = 'Пользователи'


class Project(models.Model):
    name = models.CharField(max_length=110, verbose_name='Название проекта', unique=True)
    total_square = models.FloatField(verbose_name='Общая площадь', default=0)
    author = models.CharField(max_length=100, verbose_name='Автор проекта')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    user = models.ForeignKey(
        User,  # Используем стандартного User
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        null=True,
        blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'project_tab'
        verbose_name = 'Проект'
        ordering = ['-created_at']

class Element(models.Model):
    name_element = models.CharField(max_length=110,
                            verbose_name='Тип объекта')

    def __str__(self):
        return f"{self.name_element}"

    class Meta:
        db_table = 'element_tab'
        verbose_name = 'Элемент площади'


class Property(models.Model):
    element_id = models.ForeignKey(Element,
                                    on_delete=models.CASCADE,
                                    verbose_name='Элемент площади')
    property_name = models.CharField(max_length=120,
                                     verbose_name='Характеристика')

    def __str__(self):
        return f"{self.property_name}"

    class Meta:
        db_table = 'property_tab'
        verbose_name = 'Характеристика объекта'
        verbose_name_plural = 'Характеристики объектов'


class InputData(models.Model):
    EVENT_CHOICES = [
        ('сохранение', 'Сохранение'),
        ('демонтаж', 'Демонтаж'),
        ('ремонт', 'Ремонт'),
        ('устройство', 'Устройство'),
        ('установка', 'Установка'),
        ('уничтожение', 'Уничтожение'),  # исправил опечатку
        ('восстановление', 'Восстановление'),
    ]

    project_id = models.ForeignKey(Project,
                                on_delete=models.CASCADE)
    element_id = models.ForeignKey(Element,
                                    on_delete=models.CASCADE)
    property_id = models.ForeignKey(Property,
                                        on_delete=models.CASCADE,
                                        verbose_name='Характеристика',
                                        null=False)
    square = models.FloatField(verbose_name='Площадь', null=True, blank=True)
    length = models.FloatField(verbose_name='Длина', null=True, blank=True)
    event = models.CharField(   max_length=110,
                                verbose_name='Тип работ',
                                choices=EVENT_CHOICES,
                                null=True,
                                blank=True    )

    class Meta:
        db_table = 'input_tab'
        verbose_name = 'Входные данные'

    def __str__(self):
        return f"{self.element_id}.{self.property_id} - {self.square}"