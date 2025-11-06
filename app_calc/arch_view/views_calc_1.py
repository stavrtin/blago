from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import InputData, Project, Element, Property

from django.db.models import Sum, F, Value, FloatField, Q
from django.db.models.functions import Coalesce

#
def tab_start_view(request):
    # Обработка POST запроса
    if request.method == 'POST':
        object_type_id = request.POST.get('object_type')
        property_id = request.POST.get('object_property')
        square_val = request.POST.get('square')
        length_val = request.POST.get('length')
        event_val = request.POST.get('event')

        # Валидация значения event
        valid_events = ['сохранение', 'демонтаж', 'ремонт', 'устройство',
                        'уничожение','восстановление']
        if event_val not in valid_events:
            event_val = None

        # Сохраняем данные в базу
        if object_type_id and property_id:
            InputData.objects.create(
                object_type_id=object_type_id,
                property_id=property_id,
                square=float(square_val) if square_val else None,
                length=float(length_val) if length_val else None,
                event=event_val if event_val else None
            )

        return redirect('app_calc:tab_start_view')

    # Получаем все данные для отображения
    input_data = InputData.objects.select_related('object_type', 'property').all()
    object_types = ObjectType.objects.all()

    context = {
        'input_data': input_data,
        'object_types': object_types,
        'event_choices': InputData.EVENT_CHOICES
    }

    return render(request, 'tab_start.html', context)



def get_properties(request):
    """API для получения характеристик по типу объекта"""
    object_type_id = request.GET.get('object_type_id')
    if object_type_id:
        # properties = ObjectProperty.objects.filter(object_type_id=object_type_id)
        properties = Property.objects.filter(object_type_id=object_type_id)
        properties_list = [{'id': prop.id, 'name': prop.property_name} for prop in properties]
        return JsonResponse(properties_list, safe=False)
    return JsonResponse([], safe=False)






def results_view(request):
    # -------------------- то, что введено на странице ВВОДА -------------
    input_data = InputData.objects.select_related('object_type', 'object_property').all()

    # -------------------Суммируем по Группам -****************
    input_data_total = (InputData.objects
                .values(
                'object_type__name',
                        'object_property__property_name',
                        'event')
                .annotate(
                        total_square=Sum('square') or 0.0,  # or 0.0 для обработки None
                        total_length=Sum('length') or 0.0)
                .order_by(
                'object_type__name',
                            'object_property__property_name'))

    # Заменяем None на 0 вручную после запроса
    for item in input_data_total:
        item['total_square'] = item['total_square'] or 0.0
        item['total_length'] = item['total_length'] or 0.0

    # --------------------- Демонтаж ---------------
        # Данные по демонтажу и ремонту для дорог и бордюров
    demontaj_total = InputData.objects.filter(
            # Фильтр по типу работ: демонтаж или ремонт
            Q(event='демонтаж') | Q(event='ремонт'),
            # Фильтр по типу объекта: дороги или бордюры
                    Q(object_type__name='Дорожные покрытия') | Q(object_type__name='Бортовые камни')
        ).values(
            'object_type__name',
            'object_property__property_name',
            'event'
        ).annotate(
            total_square=Coalesce(Sum('square', output_field=FloatField()), Value(0.0)),
            total_length=Coalesce(Sum('length', output_field=FloatField()), Value(0.0)),
            # Дополнительно можно добавить количество записей
            # count=Count('id')
        ).order_by('object_type__name', 'object_property__property_name')

    # --------------------- Тротуары и площадки ---------------
    # Данные по демонтажу и ремонту для дорог и бордюров
    trotuar_dorojki_total = (InputData.objects
                            .filter(
                             # Фильтр по типу работ: устройство или ремонт
                             Q(event='устройство') | Q(event='ремонт'),
                                # Фильтр по типу объекта: дороги или бордюры
                                Q(object_type__name='Дорожные покрытия') | Q(object_type__name='Бортовые камни'))
                            .values(
                                    'object_type__name',
                                    'object_property__property_name',
                                    'event')
                            .annotate(
                                    total_square=Coalesce(Sum('square', output_field=FloatField()), Value(0.0)),
                                    total_length=Coalesce(Sum('length', output_field=FloatField()), Value(0.0)),)
                                    # Дополнительно можно добавить количество записей
                                    # count=Count('id')
                            .order_by('object_type__name', 'object_property__property_name'))


    # ------------Озеленения -----------------
    total_zelenl = (InputData.objects.filter(object_type__name='Озеленение')
                    .values(
                'object_property__property_name',
                        'event')
                    .annotate(
                        total_square=Sum('square') or 0.0,)  # or 0.0 для обработки None)
                    .order_by('object_property__property_name'))

    context = {
        'input_data': input_data,
        'input_data_total': input_data_total,
        'total_zelenl':total_zelenl,
        'demontaj_total': demontaj_total,
        'trotuar_dorojki_total': trotuar_dorojki_total,
        # -----------для БАЛАНСА ------------
        'total_area': {'existing': '1000-тест', 'existing_percent': '25%-тест', 'project': '1000-test', 'project_percent': '30%'},
        'building_area': {'existing':' 500 -тест', 'existing_percent': '12.5%', 'project': '600-test', 'project_percent': '15%'},
        'road_area': {'existing': 300, 'existing_percent': '7.5%', 'project': 400, 'project_percent': '10%'},
    }

    return render(request, 'results_1.html', context)