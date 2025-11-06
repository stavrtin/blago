from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import InputData, Project, Element, Property
from django.db.models import Sum, F, Value, FloatField, Q
from django.db.models.functions import Coalesce
from django.contrib import messages  # Импортируем для сообщений об ошибках

def get_current_project(request, project_id=None):
    """
    Вспомогательная функция для получения текущего проекта.
    """
    if project_id:
        return get_object_or_404(Project, pk=project_id)
    # Если project_id не передан, используем логику по умолчанию
    return get_object_or_404(Project, pk=1)

def safe_float_conversion(value):
    """Безопасно конвертирует строку в float, возвращает None при ошибке."""
    try:
        return float(value) if value else None
    except (TypeError, ValueError):
        return None


def projects_list_view(request):
    """
    Представление для отображения списка всех проектов
    """
    projects = Project.objects.all().order_by('-created_at')

    context = {
        'projects': projects
    }
    return render(request, 'start_proj.html', context)


def new_proj_view(request):
    """
    Представление для создания нового проекта
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        total_square = request.POST.get('total_square')
        author = request.POST.get('author')

        # Валидация данных
        if not all([name, total_square, author]):
            messages.error(request, 'Все поля обязательны для заполнения')
            return render(request, 'new_proj.html')

        try:
            # Создаем новый проект
            project = Project.objects.create(
                name=name,
                total_square=float(total_square),
                author=author
            )
            messages.success(request, f'Проект "{name}" успешно создан!')
            return redirect('app_calc:tab_start_view', project_id=project.id)
        except ValueError:
            messages.error(request, 'Площадь должна быть числом')
        except Exception as e:
            messages.error(request, f'Ошибка при создании проекта: {e}')

    return render(request, 'new_proj.html')

#
# def tab_start_view(request, project_id):
#     project = get_current_project(request, project_id)
#
#     if request.method == 'POST':
#         element_id = request.POST.get('element')
#         property_id = request.POST.get('property')
#         square_val = request.POST.get('square')
#         length_val = request.POST.get('length')
#         event_val = request.POST.get('event')
#
#         valid_events = ['сохранение', 'демонтаж', 'ремонт', 'устройство', 'уничтожение', 'восстановление']
#         if event_val not in valid_events:
#             event_val = None
#
#         # Проверяем, что получены все необходимые данные
#         if not all([element_id, property_id]) or not any([square_val, length_val, event_val]):
#             messages.error(request, 'Ошибка: Не все обязательные поля заполнены.')
#         else:
#             try:
#                 # Проверяем, что элемент и свойство существуют
#                 element = Element.objects.get(pk=element_id)
#                 property_obj = Property.objects.get(pk=property_id)
#
#                 # Создаем запись
#                 InputData.objects.create(
#                     project_id=project,
#                     element_id=element,
#                     property_id=property_obj,
#                     square=safe_float_conversion(square_val),
#                     length=safe_float_conversion(length_val),
#                     event=event_val
#                 )
#                 messages.success(request, 'Данные успешно добавлены!')
#             except (Element.DoesNotExist, Property.DoesNotExist):
#                 messages.error(request, 'Ошибка: Выбранный элемент или характеристика не найдены.')
#             except Exception as e:
#                 messages.error(request, f'Произошла непредвиденная ошибка: {e}')
#
#         return redirect('app_calc:tab_start_view', project_id=project.id)
#
#     input_data = InputData.objects.filter(project_id=project).select_related('element_id', 'property_id').all()
#     elements = Element.objects.all()
#
#     context = {
#         'project': project,
#         'input_data': input_data,
#         'elements': elements,
#         'event_choices': InputData.EVENT_CHOICES
#     }
#     return render(request, 'tab_start.html', context)
#

def tab_start_view(request, project_id):
    project = get_current_project(request, project_id)

    if request.method == 'POST':
        element_id = request.POST.get('element')
        property_id = request.POST.get('property')

        # Определяем, какие данные были введены в таблице
        event_data = {}

        # Собираем данные из всех полей таблицы
        events_mapping = {
            'sohran': 'сохранение',
            'demon': 'демонтаж',
            'remont': 'ремонт',
            'ustroy': 'устройство',
            'destroy': 'уничтожение',
            'vosstan': 'восстановление'
        }

        for field_prefix, event_name in events_mapping.items():
            square_val = request.POST.get(f'square_{field_prefix}')
            length_val = request.POST.get(f'length_{field_prefix}')

            # Если есть данные для этого типа работ
            if square_val or length_val:
                event_data[event_name] = {
                    'square': safe_float_conversion(square_val),
                    'length': safe_float_conversion(length_val)
                }

        # Проверяем, что получены все необходимые данные
        if not all([element_id, property_id]) or not event_data:
            messages.error(request, 'Ошибка: Не все обязательные поля заполнены.')
        else:
            try:
                # Проверяем, что элемент и свойство существуют
                element = Element.objects.get(pk=element_id)
                property_obj = Property.objects.get(pk=property_id)

                # Создаем записи для каждого типа работ с данными
                created_count = 0
                for event_name, data in event_data.items():
                    # Создаем запись только если есть хотя бы одно значение
                    if data['square'] is not None or data['length'] is not None:
                        InputData.objects.create(
                            project_id=project,
                            element_id=element,
                            property_id=property_obj,
                            square=data['square'],
                            length=data['length'],
                            event=event_name
                        )
                        created_count += 1

                if created_count > 0:
                    messages.success(request, f'Данные успешно добавлены! Создано {created_count} записей.')
                else:
                    messages.warning(request, 'Нет данных для сохранения.')

            except (Element.DoesNotExist, Property.DoesNotExist):
                messages.error(request, 'Ошибка: Выбранный элемент или характеристика не найдены.')
            except Exception as e:
                messages.error(request, f'Произошла непредвиденная ошибка: {e}')

        return redirect('app_calc:tab_start_view', project_id=project.id)

    input_data = InputData.objects.filter(project_id=project).select_related('element_id', 'property_id').all()
    elements = Element.objects.all()

    context = {
        'project': project,
        'input_data': input_data,
        'elements': elements,
        'event_choices': InputData.EVENT_CHOICES
    }
    return render(request, 'tab_start.html', context)



def get_properties(request):
    """API для получения характеристик по элементу"""
    element_id = request.GET.get('element_id')
    if not element_id:
        return JsonResponse([], safe=False)

    try:
        properties = Property.objects.filter(element_id_id=element_id)
        properties_list = [{'id': prop.id, 'name': prop.property_name} for prop in properties]
        return JsonResponse(properties_list, safe=False)
    except Exception as e:
        # Логируем ошибку (e) для дебага
        return JsonResponse([], safe=False)

def calculate_totals(queryset):
    """Вспомогательная функция для ручной замены None на 0 в аннотированных полях."""
    for item in queryset:
        item['total_square'] = item['total_square'] or 0.0
        item['total_length'] = item['total_length'] or 0.0
    return queryset

def results_view(request, project_id):
    # project = get_current_project(request)
    project = get_current_project(request, project_id)

    input_data = InputData.objects.filter(project_id=project).select_related('element_id', 'property_id').all()

    # -------------------Суммируем по Группам -----------------
    input_data_total = (InputData.objects
                        .filter(project_id=project)
                        .values('element_id__name_element', 'property_id__property_name', 'event')
                        .annotate(
                            total_square=Sum('square'),
                            total_length=Sum('length')
                        ).order_by('element_id__name_element', 'property_id__property_name'))
    input_data_total = calculate_totals(input_data_total)

    # --------------------- Демонтаж ---------------
    demontaj_filter = Q(project_id=project) & (Q(event='демонтаж') | Q(event='ремонт')) & (Q(element_id__name_element='Дорожные покрытия') | Q(element_id__name_element='Бортовые камни'))
    demontaj_total = (InputData.objects
                      .filter(demontaj_filter)
                      .values('element_id__name_element', 'property_id__property_name', 'event')
                      .annotate(
                          total_square=Coalesce(Sum('square', default=0.0), Value(0.0, output_field=FloatField())),
                          total_length=Coalesce(Sum('length', default=0.0), Value(0.0, output_field=FloatField())),
                      ).order_by('element_id__name_element', 'property_id__property_name'))

    # --------------------- Тротуары и площадки ---------------
    trotuar_filter = Q(project_id=project) & (Q(event='устройство') | Q(event='ремонт')) & (Q(element_id__name_element='Дорожные покрытия') | Q(element_id__name_element='Бортовые камни'))
    trotuar_dorojki_total = (InputData.objects
                             .filter(trotuar_filter)
                             .values('element_id__name_element', 'property_id__property_name', 'event')
                             .annotate(
                                 total_square=Coalesce(Sum('square', default=0.0), Value(0.0, output_field=FloatField())),
                                 total_length=Coalesce(Sum('length', default=0.0), Value(0.0, output_field=FloatField())),
                             ).order_by('element_id__name_element', 'property_id__property_name'))

    # ------------Озеленения -----------------
    total_zelenl = (InputData.objects.filter(project_id=project, element_id__name_element='Озеленение')
                    .values('property_id__property_name', 'event')
                    .annotate(total_square=Sum('square'))
                    .order_by('property_id__property_name'))
    total_zelenl = calculate_totals(total_zelenl)

    context = {
        'project': project,
        'input_data': input_data,
        'input_data_total': input_data_total,
        'total_zelenl': total_zelenl,
        'demontaj_total': demontaj_total,
        'trotuar_dorojki_total': trotuar_dorojki_total,
        'total_area': {'existing': '1000-тест', 'existing_percent': '25%-тест', 'project': '1000-test', 'project_percent': '30%'},
        'building_area': {'existing': ' 500 -тест', 'existing_percent': '12.5%', 'project': '600-test', 'project_percent': '15%'},
        'road_area': {'existing': 300, 'existing_percent': '7.5%', 'project': 400, 'project_percent': '10%'},
    }
    return render(request, 'results_1.html', context)