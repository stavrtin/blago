from django.shortcuts import render
from django.http import JsonResponse
from .models import ConstructionData
from decimal import Decimal


def calculate_totals(request):
    # Данные из JSON (можно получать через API или форму)
    json_data = {
        'Здания и сооружения.Здания': 100,
        'Здания и сооружения.Лестницы': 34,
        'Здания и сооружения.Подпорные': 23,
        'Покрытия.асфальтобетов': 34,
        'Покрытия.бетон': 12,
        'Покрытия.Тротуар': 43,
        'Покрытия.бортовой камень БР 100.30.15': 56,
        'Озеленения.газон': 23,
        'Озеленения.цветники': 12,
    }

    # Обрабатываем данные
    categories = {}
    total_area = Decimal('0')

    for key, value in json_data.items():
        category, subcategory = key.split('.', 1)
        area = Decimal(str(value))

        if category not in categories:
            categories[category] = {
                'subcategories': [],
                'total_area': Decimal('0'),
                'percentage': Decimal('0')
            }

        categories[category]['subcategories'].append({
            'name': subcategory,
            'area': area
        })
        categories[category]['total_area'] += area
        total_area += area

    # Рассчитываем проценты
    for category in categories.values():
        if total_area > 0:
            category['percentage'] = (category['total_area'] / total_area * 100).quantize(Decimal('0.01'))
        else:
            category['percentage'] = Decimal('0')

    # Подготавливаем данные для таблицы
    table_data = []
    for category_name, category_data in categories.items():
        # Добавляем заголовок категории
        table_data.append({
            'type': 'header',
            'category': category_name,
            'total_area': category_data['total_area'],
            'percentage': category_data['percentage']
        })

        # Добавляем подкатегории
        for subcategory in category_data['subcategories']:
            table_data.append({
                'type': 'subcategory',
                'name': subcategory['name'],
                'area': subcategory['area']
            })

    context = {
        'table_data': table_data,
        'total_area': total_area,
        'categories': categories
    }

    return render(request, 'total.html', context)


# views.py (альтернативная версия)
def calculate_totals_advanced(request):
    json_data = {
        'Здания и сооружения.Здания': 100,
        'Здания и сооружения.Лестницы': 34,
        'Здания и сооружения.Подпорные': 23,
        'Покрытия.асфальтобетов': 34,
        'Покрытия.бетон': 12,
        'Покрытия.Тротуар': 43,
        'Покрытия.бортовой камень БР 100.30.15': 56,
        'Озеленения.газон': 23,
        'Озеленения.цветники': 12,
    }

    # Рассчитываем суммы по категориям
    buildings_total = sum([v for k, v in json_data.items() if k.startswith('Здания и сооружения')])
    coverings_total = sum([v for k, v in json_data.items() if k.startswith('Покрытия')])
    landscaping_total = sum([v for k, v in json_data.items() if k.startswith('Озеленения')])

    total_area = buildings_total + coverings_total + landscaping_total

    # Рассчитываем проценты
    buildings_percentage = (buildings_total / total_area * 100) if total_area else 0
    coverings_percentage = (coverings_total / total_area * 100) if total_area else 0
    landscaping_percentage = (landscaping_total / total_area * 100) if total_area else 0

    context = {
        'json_data': json_data,
        'buildings_total': buildings_total,
        'coverings_total': coverings_total,
        'landscaping_total': landscaping_total,
        'total_area': total_area,
        'buildings_percentage': round(buildings_percentage, 2),
        'coverings_percentage': round(coverings_percentage, 2),
        'landscaping_percentage': round(landscaping_percentage, 2),
    }

    return render(request, 'total_advanced.html', context)
