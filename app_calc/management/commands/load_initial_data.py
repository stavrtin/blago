from django.core.management.base import BaseCommand
from app_calc.models import ObjectType, ObjectProperty


class Command(BaseCommand):
    help = 'Load initial object types and properties'

    def handle(self, *args, **options):
        # Создаем типы объектов
        road_type, created = ObjectType.objects.get_or_create(name='Дорожные покрытия')
        greenery_type, created = ObjectType.objects.get_or_create(name='Озеленение')
        curb_type, created = ObjectType.objects.get_or_create(name='Бортовые камни')

        # Характеристики для дорог
        road_properties = [
            'асфальтобетон (проезд)',
            'асфальтобетон (тротуар)',
            'цементнобетонное покрытие',
            'бетонная плитка',
            'гранитная плитка',
            'гравийный отсев',
            'гранитный отсев',
            'резиновое покрытие',
            'TerraWay',
        ]

        # Характеристики для озеленения
        greenery_properties = [
            'газон/травяной покров',
            'цветник'
        ]

        # Характеристики для бордюров
        curb_properties = [
            'бетонный',
            'гранитный',
            'пластиковый',
            'металлический'
        ]

        # Создаем характеристики
        for prop in road_properties:
            ObjectProperty.objects.get_or_create(object_type=road_type, property_name=prop)

        for prop in greenery_properties:
            ObjectProperty.objects.get_or_create(object_type=greenery_type, property_name=prop)

        for prop in curb_properties:
            ObjectProperty.objects.get_or_create(object_type=curb_type, property_name=prop)

        self.stdout.write(self.style.SUCCESS('Initial data loaded successfully'))