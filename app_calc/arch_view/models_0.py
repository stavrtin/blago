from django.db import models
from django.contrib.auth.models import User

# class UserLogin(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     login_time = models.DateTimeField(auto_now_add=True)
#
#     def __str__(self):
#         return f"{self.user.username} logged in at {self.login_time}"


class DataFields(models.Model):
    object = models.CharField(max_length=100, verbose_name='Объект', )
    property = models.CharField(max_length=100, verbose_name='Характеристика',null=True)
    square = models.FloatField(verbose_name='Площадь',null=True)
    length = models.FloatField(verbose_name='Длина',null=True)
    event = models.CharField(verbose_name='Тип_работ',null=True)
    # photo = models.ImageField(
    #     verbose_name='Фотография',
    #     upload_to='business_cards/',
    #     blank=True,
    #     null=True,
    #     help_text='Загрузите фотографию в формате JPEG'
    #                              )
    def __str__(self):
        return f"{self.object} - {self.property}"

    class Meta:
        db_table = 'object_tab'  # Указываем имя таблицы в БД
        verbose_name = 'Работа'
        verbose_name_plural = 'Работа'

class InputData(models.Model):
    EVENT_CHOICES = [
        ('сохранение', 'Сохранение'),
        ('демонтаж', 'Демонтаж'),
        ('ремонт', 'Ремонт'),
        ('устройство', 'Устройство'),
    ]

    OBJECT_CHOICES = [
        ('дор_покрытие', 'Дорожное покрытие'),
        ('борт_камни', 'Бортовые камни'),
        ('озеленение', 'Озеленение'),
        ('подп_стенки', 'Подп_стенки'),
        ('лестницы', 'Лестницы'),

    ]
    object =  models.CharField(
                    max_length=100,
                    verbose_name='Объект',
                    choices=OBJECT_CHOICES,
                    null=True,
                    blank=True
                )
    property = models.CharField(max_length=100, verbose_name='Характеристика', null=True, blank=True)
    square = models.FloatField(verbose_name='Площадь', null=True, blank=True)
    length = models.FloatField(verbose_name='Длина', null=True, blank=True)
    event = models.CharField(
        max_length=100,
        verbose_name='Тип работ',
        choices=EVENT_CHOICES,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        db_table = 'input_tab'  # Указываем имя таблицы в БД
        verbose_name = 'Входные данные'
        verbose_name_plural = 'Входные данные'
        ordering = ['-created_at']

    def __str__(self):
        return self.object



from django.db import models

# Create your models here.