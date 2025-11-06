from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import InputData, Project, Element, Property
from django.db.models import Sum, F, Value, FloatField, Q
from django.db.models.functions import Coalesce
from django.contrib import messages  # Импортируем для сообщений об ошибках

import pandas as pd


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


def tab_start_view(request, project_id):
    project = get_current_project(request, project_id)

    if request.method == 'POST':
        element_id = request.POST.get('element')
        property_id = request.POST.get('property')

        # Определяем, какие данные были введены в таблице
        event_data = {}

        # Маппинг префиксов таблиц и соответствующих событий
        table_mappings = {
            'pokr': {  # Покрытия и здания
                'sohran': 'сохранение',
                'demon': 'демонтаж',
                'remont': 'ремонт',
                'ustroy': 'устройство'
            },
            'bort': {  # Бортовой камень
                'demon': 'демонтаж',
                'sohran': 'сохранение',
                # 'vosstan': 'восстановление',
                 'ustroy': 'установка'
            },
            'ozel': {  # Озеленение
                'destroy': 'уничтожение',
                'ustroy': 'устройство',
                'sohran': 'сохранение',
                'vosstan': 'восстановление'
            }
        }

        # Определяем, какая таблица активна (по выбранному элементу)
        try:
            element = Element.objects.get(pk=element_id) if element_id else None
            element_name = element.name_element if element else ""
        except Element.DoesNotExist:
            element_name = ""

        if element and ('Покрытия' in element_name or 'Здания' in element_name):
            table_prefix = 'pokr'
        elif element and 'Бортовой' in element_name:
            table_prefix = 'bort'
        elif element and 'Озеленение' in element_name:
            table_prefix = 'ozel'
        else:
            table_prefix = None

        if table_prefix:
            for field_suffix, event_name in table_mappings[table_prefix].items():
                square_val = request.POST.get(f'square_{field_suffix}_{table_prefix}')
                length_val = request.POST.get(f'length_{field_suffix}_{table_prefix}')

                # Для бортового камня проверяем оба поля
                if table_prefix == 'bort':
                    if square_val or length_val:  # Хотя бы одно поле заполнено
                        event_data[event_name] = {
                            'square': safe_float_conversion(square_val),
                            'length': safe_float_conversion(length_val)
                        }
                # Для других таблиц проверяем только площадь (длина всегда 0 через hidden)
                else:
                    if square_val:  # Только если площадь заполнена
                        event_data[event_name] = {
                            'square': safe_float_conversion(square_val),
                            'length': 0.0  # Для покрытий и озеленения длина всегда 0
                        }

        # Проверяем, что получены все необходимые данные
        if not all([element_id, property_id]):
            messages.error(request, 'Ошибка: Не все обязательные поля заполнены.')
        else:
            try:
                # Проверяем, что элемент и свойство существуют
                element = Element.objects.get(pk=element_id)
                property_obj = Property.objects.get(pk=property_id)

                # Создаем записи для каждого типа работ с данными
                created_count = 0
                for event_name, data in event_data.items():
                    # Создаем запись только если есть данные
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
        # item['total_length'] = item['total_length'] or 0.0
    return queryset


def calcilate_zelen_summ(data_from_ozelenen):
    # --------------ВЫЧИСЛЕНИЕ озеленения (без уничтожения)
    # ---------------на выходе словарь--- {'Газон/травяной покров': 45.0, 'Цветники': 50.0}

    df = pd.DataFrame(data_from_ozelenen)
    df_res = (df.loc[df['event']
                            .isin(['сохранение', 'устройство', 'восстановление'])]
                            .groupby('property_id__property_name')
                            .agg({'total_square': 'sum'}))

    dict_exit = df_res.to_dict().get('total_square')
    print(f'{dict_exit=}')
    return dict_exit

def marker_destroy(data_from_ozelenen):
    # --------------ВЫЧИСЛЕНИЕ признака наличия строки "уничтожение"
    # -------------- для передачи в шаблон переменной (collaps) , важной для объединения ячейки
    # ---------------на выходе словарь--- {'Газон/травяной покров': 1, 'Цветники': 0}
    # 1 - есть уничтож, 0-нет такой позиции

    df_destroy = pd.DataFrame(data_from_ozelenen)

    df_destroy['marker'] = 0
    df_destroy.loc[df_destroy.event == 'уничтожение', 'marker'] = 1
    df_destroy_mark = df_destroy.loc[df_destroy.marker == 1]
    df_res = pd.merge(df_destroy[['property_id__property_name', 'event', 'total_square']],
                      df_destroy_mark[['property_id__property_name', 'marker']], how='left',
                      left_on=['property_id__property_name'], right_on=['property_id__property_name'])

    dict_exit = df_res.to_dict().get('total_square')
    return dict_exit




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
    demontaj_filter = Q(project_id=project) & (Q(event='демонтаж') | Q(event='ремонт')) & (Q(element_id__name_element='Покрытия') | Q(element_id__name_element='Бортовой камень'))
    demontaj_total = (InputData.objects
                      .filter(demontaj_filter)
                      .values('element_id__name_element', 'property_id__property_name', 'event')
                      .annotate(
                          total_square=Coalesce(Sum('square', default=0.0), Value(0.0, output_field=FloatField())),
                          total_length=Coalesce(Sum('length', default=0.0), Value(0.0, output_field=FloatField())),
                      ).order_by('element_id__name_element', 'property_id__property_name'))

    # --------------------- Тротуары и площадки ---------------
    trotuar_filter = Q(project_id=project) & (Q(event='устройство') | Q(event='ремонт')) & (Q(element_id__name_element='Покрытия') | Q(element_id__name_element='Бортовой камень'))
    trotuar_dorojki_total = (InputData.objects
                             .filter(trotuar_filter)
                             .values('element_id__name_element', 'property_id__property_name', 'event')
                             .annotate(
                                 total_square=Coalesce(Sum('square', default=0.0), Value(0.0, output_field=FloatField())),
                                 total_length=Coalesce(Sum('length', default=0.0), Value(0.0, output_field=FloatField())),
                             ).order_by('element_id__name_element', 'property_id__property_name'))

    # ------------Озеленения -----------------
    total_zelenl = (InputData.objects.filter(project_id=project, element_id__name_element='Озеленение (обводнение)')
                    .values('property_id__property_name', 'event')
                    .annotate(total_square=Sum('square'))
                    .order_by('property_id__property_name'))

    # ---- создать список/словарь, что у Типа есть уничтожение--------
    results = (InputData.objects.filter(project_id=project, element_id__name_element='Озеленение (обводнение)')
                    .values('property_id__property_name', 'event')
                    .order_by('property_id__property_name'))
    print(results)
    dict_list_of_mark_destr = []
    mark_of_destr = 0
    for i_prop in results:
        if i_prop.event == 'уничтожение':
            mark_of_destr = 1
            dict_list_of_mark_destr.append({'i_prop.element_id_id__name_element':'i_prop', 'mark_of_destr':1})
        else: dict_list_of_mark_destr.append({'i_prop.element_id_id__name_element':'i_prop', 'mark_of_destr':0})




    # ---------------------------------------------------------------таблица ГАЗОНОВ н-
    # Обрабатываем данные для озеленения с подсчетом сумм
    processed_zelenl = []
    zelenl_sums = {}
    # zelenl_totals = {
    #     'уничтожение': 0,
    #     'устройство': 0,
    #     'восстановление': 0,
    #     'сохранение': 0,
    #     'total_without_destroy': 0
    # }

    # for item in total_zelenl:
    #     prop_name = item['property_id__property_name']
    #     event = item['event']
    #     square = item['total_square'] or 0
    #
    #     # Суммируем по событиям
    #     zelenl_totals[event] += square
    #
    #     # Суммируем только устройство, сохранение, восстановление
    #     if event in ['устройство', 'сохранение', 'восстановление']:
    #         zelenl_totals['total_without_destroy'] += square
    #     # ---------------mark of destroy ------
    #         zelenl_totals['mark_ofdestroy'] = +1
    #     else: zelenl_totals['total_without_destroy'] += square
    #
    #     processed_zelenl.append(item)
        # ---------------------------------------------------------------таблица ГАЗОНОВ к-

    zelen_summ = calcilate_zelen_summ(total_zelenl) #-----вычислим суммы для озеленения
    # collaps_destroy = marker_destroy(total_zelenl) #-----вычислим переменную COLLAPS - для объединения ячейки

    context = {
        'project': project,
        'input_data': input_data,
        'input_data_total': input_data_total,
        'total_zelenl': total_zelenl,
        # 'total_zelenl1': zelenl_totals,

        # 'total_zelenl_p': processed_zelenl,
        'results': results,
        # 'dict_list_of_mark_destr': dict_list_of_mark_destr,
        'calcilate_zelen_summ': zelen_summ,

        # 'collaps_destroy':collaps_destroy,
        'ssss':0,
        'demontaj_total': demontaj_total,
        'demontaj_filter': demontaj_filter,
        'trotuar_dorojki_total': trotuar_dorojki_total,
        'total_area': {'existing': '1000-тест', 'existing_percent': '25%-тест', 'project': '1000-test', 'project_percent': '30%'},
        'building_area': {'existing': ' 500 -тест', 'existing_percent': '12.5%', 'project': '600-test', 'project_percent': '15%'},
        'road_area': {'existing': 300, 'existing_percent': '7.5%', 'project': 400, 'project_percent': '10%'},
    }
    return render(request, 'results_1.html', context)


