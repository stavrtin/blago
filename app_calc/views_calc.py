from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F, Value, FloatField, Q
from django.db.models.functions import Coalesce
from .models import InputData, Project, Element, Property
# from .forms import CustomUserCreationForm, CustomAuthenticationForm
from .forms import SimpleUserCreationForm, CustomAuthenticationForm

import pandas as pd


def start_login_view(request):
    """Представление для страницы входа"""
    if request.user.is_authenticated:
        return redirect('app_calc:projects_list')

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('app_calc:projects_list')
            else:
                messages.error(request, 'Неверный логин или пароль')
        else:
            messages.error(request, 'Ошибка в форме входа')
    else:
        form = CustomAuthenticationForm()

    context = {
        'form': form
    }
    return render(request, 'start_login.html', context)


def start_register_view(request):
    """Представление для страницы регистрации"""
    if request.user.is_authenticated:
        return redirect('app_calc:projects_list')

    if request.method == 'POST':
        form = SimpleUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, f'Аккаунт создан! Добро пожаловать, {user.username}!')
                return redirect('app_calc:projects_list')
            except Exception as e:
                messages.error(request, f'Ошибка при создании пользователя: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = SimpleUserCreationForm()

    context = {
        'form': form
    }
    return render(request, 'start_register.html', context)


def logout_view(request):
    """Выход из системы"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('app_calc:start_login')


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

@login_required
def projects_list_view(request):
    """Список проектов только текущего пользователя"""
    projects = Project.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'projects': projects
    }
    return render(request, 'start_proj.html', context)

@login_required
def new_proj_view(request):
    """Создание нового проекта для текущего пользователя"""
    if request.method == 'POST':
        name = request.POST.get('name')
        total_square = request.POST.get('total_square')
        # author = request.POST.get('author')

        # Валидация данных
        if not all([name, total_square,
                    # author
                    ]):
            messages.error(request, 'Все поля обязательны для заполнения')
            return render(request, 'new_proj.html')

        try:
            # Создаем новый проект для текущего пользователя
            project = Project.objects.create(
                name=name,
                total_square=float(total_square),
                author=request.user,
                user=request.user  # Привязываем проект к текущему пользователю
            )
            messages.success(request, f'Проект "{name}" успешно создан!')
            return redirect('app_calc:tab_start_view', project_id=project.id)
        except ValueError:
            messages.error(request, 'Площадь должна быть числом')
        except Exception as e:
            messages.error(request, f'Ошибка при создании проекта: {e}')

    return render(request, 'new_proj.html')

@login_required
def tab_start_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id, user=request.user)

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

    input_data = (InputData.objects
                  .filter(project_id=project)
                  .select_related('element_id', 'property_id')
                  .order_by('element_id__name_element', 'property_id__property_name' ))

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
    if not data_from_ozelenen:
        return {}

    try:
        df = pd.DataFrame(data_from_ozelenen)

        # Проверяем наличие необходимых колонок
        if 'event' not in df.columns or 'property_id__property_name' not in df.columns or 'total_square' not in df.columns:
            return {}

        df_res = (df.loc[df['event']
                  .isin(['сохранение', 'устройство', 'восстановление'])]
                  .groupby('property_id__property_name')
                  .agg({'total_square': 'sum'}))

        dict_exit = df_res.to_dict().get('total_square', {})
        print(f'{dict_exit=}')
        return dict_exit
    except Exception as e:
        print(f"Ошибка в calcilate_zelen_summ: {e}")
        return {}

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

def calculate_totals_balance(json_data):
    if not json_data:
        return [{}, {}]

    try:
        df_start = pd.DataFrame(json_data)

        # Проверяем наличие необходимых колонок
        required_columns = ['event', 'element_id__name_element', 'property_id__property_name', 'total_square']
        for col in required_columns:
            if col not in df_start.columns:
                return [{}, {}]

        df_bez_zelet_now = df_start.loc[df_start.event.isin(['сохранение', 'демонтаж', 'ремонт', 'установка'])
                                        & ~df_start.element_id__name_element.isin(['Озеленение (обводнение)'])]

        df_zelen_now = df_start.loc[df_start.event.isin(['сохранение', 'уничтожение', 'восстановление'])
                                    & df_start.element_id__name_element.isin(['Озеленение (обводнение)'])]

        df_now = pd.concat([df_bez_zelet_now, df_zelen_now])

        df_bez_zelet_proj = df_start.loc[df_start.event.isin(['сохранение', 'устройство', 'ремонт', 'установка'])
                                         & ~df_start.element_id__name_element.isin(['Озеленение (обводнение)'])]

        df_zelen_proj = df_start.loc[df_start.event.isin(['сохранение', 'устройство', 'восстановление', 'установка'])
                                     & df_start.element_id__name_element.isin(['Озеленение (обводнение)'])]

        df_proj = pd.concat([df_bez_zelet_proj, df_zelen_proj])

        dict_now = df_now.groupby(['element_id__name_element', 'property_id__property_name']).agg(
            {'total_square': 'sum'}).to_dict()
        result_dict_now = {f"{element}.{property_name}": value for (element, property_name), value in
                           dict_now['total_square'].items()}

        dict_proj = df_proj.groupby(['element_id__name_element', 'property_id__property_name']).agg(
            {'total_square': 'sum'}).to_dict()
        result_dict_proj = {f"{element}.{property_name}": value for (element, property_name), value in
                            dict_proj['total_square'].items()}

        return [result_dict_now, result_dict_proj]
    except Exception as e:
        print(f"Ошибка в calculate_totals_balance: {e}")
        return [{}, {}]

@login_required
def results_view(request, project_id):
    # Добавляем проверку, что проект принадлежит пользователю
    project = get_object_or_404(Project, pk=project_id, user=request.user)

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

    # # categories_dict = demontaj_total(list)
    # categories_dict = demontaj_total
    # Группируем данные по категориям (замена defaultdict)
    categories_dict = {}
    counter = 1

    for item in demontaj_total:
        category_name = item['element_id__name_element']
        #
        # # Создаем запись для категории, если ее еще нет
        if category_name not in categories_dict:
            categories_dict[category_name] = []

        # Добавляем элемент в категорию (только площадь, без длины)
        item_data = {
            'number': str(counter),
            # 'name': f"{category_name} - {item['property_id__property_name']}",
            'name': f"{item['property_id__property_name']}",
            'area': f"{item['total_square']:.1f}",
            'note': item['event']
        }
        categories_dict[category_name].append(item_data)
        counter += 1

    # Преобразуем в структуру для шаблона
    categories = [{'name': name, 'items': items} for name, items in categories_dict.items()]

    # Подсчет общего количества позиций
    total_items = sum(len(category['items']) for category in categories)



    # --------------------- Тротуары и площадки ---------------
    trotuar_filter = (Q(project_id=project)
                      & (Q(event='устройство') | Q(event='ремонт'))
                      & (Q(element_id__name_element='Покрытия') | Q(element_id__name_element='Бортовой камень')))
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

    # ------------------ Создание признака УНИЧТОЖЕНИЕ- для формирования
    # ------------ переменной, участвующей в шаблоне для объединения
    # ---------------------ячеек  <td rowspan="{{ property.list|length|add:'-1' }}" style="background-color:....">
    if total_zelenl:
        destroyed_properties = []
        for item in total_zelenl:
                # destroyed_properties.add(item['property_id__property_name'])
                destroyed_properties.append(item['property_id__property_name'])


        for item in total_zelenl:
            property_name = item['property_id__property_name']
            if property_name in destroyed_properties:
                # Если свойство есть в множестве уничтоженных, ставим -1, иначе 0
                # dict_new[property_name] = -1 if property_name in destroyed_properties else 0
                item['mark_of_destroy'] = -1 # если есть "уничтожение"
            else: item['mark_of_destroy'] = 0 # если есть "уничтожение"

        # ---------------------------------------------------------------таблица ГАЗОНОВ н-
        zelen_summ = calcilate_zelen_summ(total_zelenl) #-----вычислим суммы для озеленения
    else:
        zelen_summ = {}


    # ------------------------------сбор БАЛАНСОВ всего, что есть , с группировкой для упрщен --1нач
    # -------------------- пробуем json для вывода Балансов -*-----------------
    all_input_data = (InputData.objects
                    .filter(project_id=project)
                    .select_related('element_id', 'property_id')
                    .values(
        'element_id__name_element',
        'property_id__property_name',
        'event'
    )
                    .annotate(
        total_square=Coalesce(Sum('square'), Value(0.0, output_field=FloatField())),
        total_length=Coalesce(Sum('length'), Value(0.0, output_field=FloatField()))
    )
                    .order_by('element_id__name_element', 'property_id__property_name', 'event')
                    )

    all_input_data = list(all_input_data)

    # --------------- баланс - СУЩЕСТВУЮЩИЙ и ПРОЕКТИРУЕМЫЙ ---------------
    json_now_balance = calculate_totals_balance(all_input_data)[0]
    json_project_balance = calculate_totals_balance(all_input_data)[1]

    # ----------------------------------СУЩЕСТВУЮЩИЙ-------------------------------
    # -----------------------Рассчитываем суммы по категориям СУЩЕСТВУЮЩИЙ
    buildings_total_now = sum([v for k, v in json_now_balance.items() if k.startswith('Здания и сооружения')])
    coverings_total_now = sum([v for k, v in json_now_balance.items() if k.startswith('Покрытия')])
    landscaping_total_now = sum([v for k, v in json_now_balance.items() if k.startswith('Озеленение (обводнение).')])
    stone_total_now = sum([v for k, v in json_now_balance.items() if k.startswith('Бортовой камень')])

    total_area_now = buildings_total_now + coverings_total_now + landscaping_total_now + stone_total_now

    # Рассчитываем проценты----СУЩЕСТВУЮЩИЙ --------
    buildings_percentage_now = (buildings_total_now / total_area_now * 100) if total_area_now else 0
    coverings_percentage_now = (coverings_total_now / total_area_now * 100) if total_area_now else 0
    landscaping_percentage_now = (landscaping_total_now / total_area_now * 100) if total_area_now else 0
    stone_percentage_now = (stone_total_now / total_area_now * 100) if total_area_now else 0


    # ----------------------------------ПРОЕКТНЫЙ-------------------------------
    # -----------------------Рассчитываем суммы по категориям ПРОЕКТНЫЙ
    buildings_total_proj = sum([v for k, v in json_project_balance.items() if k.startswith('Здания и сооружения')])
    coverings_total_proj = sum([v for k, v in json_project_balance.items() if k.startswith('Покрытия')])
    landscaping_total_proj = sum([v for k, v in json_project_balance.items() if k.startswith('Озеленение (обводнение).')])
    stone_total_proj = sum([v for k, v in json_project_balance.items() if k.startswith('Бортовой камень')])

    total_area_proj = buildings_total_proj + coverings_total_proj + landscaping_total_proj + stone_total_proj

    # Рассчитываем проценты----ПРОЕКТНЫЙ --------
    buildings_percentage_proj = (buildings_total_proj / total_area_proj * 100) if total_area_proj else 0
    coverings_percentage_proj = (coverings_total_proj / total_area_proj * 100) if total_area_proj else 0
    landscaping_percentage_proj = (landscaping_total_proj / total_area_proj * 100) if total_area_proj else 0
    stone_percentage_proj = (stone_total_proj / total_area_proj * 100) if total_area_proj else 0


    # ------------------------------сбор всего, что есть , с группировкой для упрщен --1кон
    delta_now_proj = total_area_now - total_area_proj

    # --------------- Собранный json для формирования БАЛАНСОВ ----------
    unique_name_objects = list(set(json_now_balance.keys()) | set(json_project_balance.keys()))
    # -----------------создаем словарь, в котром в значении - список
    dict_now_proj = {key: [None, None] for key in unique_name_objects}


    # -------------------Наполняем словарь значениями из сууществующих -------
    for name_obj in unique_name_objects:
        if name_obj in list(set(json_now_balance.keys())):
            # print(dict1.get(name_obj))
            dict_now_proj[name_obj][0] = json_now_balance.get(name_obj)
        else:
            dict_now_proj[name_obj][0] = None

    # -------------------------Наполняем словарь значениями  для проектных

    for name_obj in unique_name_objects:
        if name_obj in list(set(json_project_balance.keys())):
            # print(dict1.get(name_obj))
            dict_now_proj[name_obj][1] = json_project_balance.get(name_obj)
        else:
            dict_now_proj[name_obj][1] = None

    # input_square =  (Project.objects.filter(project_id=project).values('total_square'))
    input_square =  ((Project.objects.filter(id=project.id)
                     .values('total_square'))
                     .first())

    context = {
        'project': project,
        'input_data_now': json_now_balance,
        'input_data_project': json_project_balance,
        'input_data_total': input_data_total,
        'total_zelenl': total_zelenl,

        'result_list': destroyed_properties,
        'calcilate_zelen_summ': zelen_summ,

        'demontaj_total': demontaj_total,
        'categories':categories,

        'demontaj_filter': demontaj_filter,
        'trotuar_dorojki_total': trotuar_dorojki_total,

        # -----------------------------вывод в балансы ---------------
        'json_data_now_and_proj': dict_now_proj,
        # --------------------------Существующ -----------------------
        'json_now_balance': json_now_balance,
        'buildings_total_now': buildings_total_now,
        'coverings_total_now': coverings_total_now,
        'landscaping_total_now': landscaping_total_now,
        'stone_total_now': stone_total_now,

        'buildings_percentage_now': buildings_percentage_now,
        'coverings_percentage_now': coverings_percentage_now,
        'landscaping_percentage_now': landscaping_percentage_now,
        'stone_percentage_now': stone_percentage_now,

        'total_area_now': total_area_now,

        # --------------------------Проектн -----------------------
        'json_project_balance':json_project_balance,
        'buildings_total_proj':buildings_total_proj,
        'coverings_total_proj':coverings_total_proj,
        'landscaping_total_proj':landscaping_total_proj,
        'stone_total_proj':stone_total_proj,

        'buildings_percentage_proj':buildings_percentage_proj,
        'coverings_percentage_proj':coverings_percentage_proj,
        'landscaping_percentage_proj':landscaping_percentage_proj,
        'stone_percentage_proj':stone_percentage_proj,

        'total_area_proj':total_area_proj,
        'delta_now_proj':delta_now_proj,
        'input_square':input_square,


    }
    return render(request, 'results_1.html', context)
    # return render(request, 'res_1.html', context)


# ---------------------------------------------------------Сравнительные балансы ----------------------------------
@login_required
def results_balance_view(request, project_id):
    # Добавляем проверку, что проект принадлежит пользователю
    project = get_object_or_404(Project, pk=project_id, user=request.user)

    # -------------------Суммируем по Группам -----------------
    input_data_total = (InputData.objects
                        .filter(project_id=project)
                        .values('element_id__name_element', 'property_id__property_name', 'event')
                        .annotate(
                            total_square=Sum('square'),
                            total_length=Sum('length')
                        ).order_by('element_id__name_element', 'property_id__property_name'))
    input_data_total = calculate_totals(input_data_total)

    # ------------------------------сбор БАЛАНСОВ всего, что есть , с группировкой для упрщен --1нач
    # -------------------- пробуем json для вывода Балансов -*-----------------
    all_input_data = (InputData.objects
                    .filter(project_id=project)
                    .select_related('element_id', 'property_id')
                    .values(
        'element_id__name_element',
        'property_id__property_name',
        'event'
    )
                    .annotate(
        total_square=Coalesce(Sum('square'), Value(0.0, output_field=FloatField())),
        total_length=Coalesce(Sum('length'), Value(0.0, output_field=FloatField()))
    )
                    .order_by('element_id__name_element', 'property_id__property_name', 'event')
                    )

    all_input_data = list(all_input_data)

    # --------------- баланс - СУЩЕСТВУЮЩИЙ и ПРОЕКТИРУЕМЫЙ ---------------
    json_now_balance = calculate_totals_balance(all_input_data)[0]
    json_project_balance = calculate_totals_balance(all_input_data)[1]

    # ----------------------------------СУЩЕСТВУЮЩИЙ-------------------------------
    # -----------------------Рассчитываем суммы по категориям СУЩЕСТВУЮЩИЙ
    buildings_total_now = sum([v for k, v in json_now_balance.items() if k.startswith('Здания и сооружения')])
    coverings_total_now = sum([v for k, v in json_now_balance.items() if k.startswith('Покрытия')])
    landscaping_total_now = sum([v for k, v in json_now_balance.items() if k.startswith('Озеленение (обводнение).')])
    stone_total_now = sum([v for k, v in json_now_balance.items() if k.startswith('Бортовой камень')])

    total_area_now = buildings_total_now + coverings_total_now + landscaping_total_now + stone_total_now

    # Рассчитываем проценты----СУЩЕСТВУЮЩИЙ --------
    buildings_percentage_now = (buildings_total_now / total_area_now * 100) if total_area_now else 0
    coverings_percentage_now = (coverings_total_now / total_area_now * 100) if total_area_now else 0
    landscaping_percentage_now = (landscaping_total_now / total_area_now * 100) if total_area_now else 0
    stone_percentage_now = (stone_total_now / total_area_now * 100) if total_area_now else 0


    # ----------------------------------ПРОЕКТНЫЙ-------------------------------
    # -----------------------Рассчитываем суммы по категориям ПРОЕКТНЫЙ
    buildings_total_proj = sum([v for k, v in json_project_balance.items() if k.startswith('Здания и сооружения')])
    coverings_total_proj = sum([v for k, v in json_project_balance.items() if k.startswith('Покрытия')])
    landscaping_total_proj = sum([v for k, v in json_project_balance.items() if k.startswith('Озеленение (обводнение).')])
    stone_total_proj = sum([v for k, v in json_project_balance.items() if k.startswith('Бортовой камень')])

    total_area_proj = buildings_total_proj + coverings_total_proj + landscaping_total_proj + stone_total_proj

    # Рассчитываем проценты----ПРОЕКТНЫЙ --------
    buildings_percentage_proj = (buildings_total_proj / total_area_proj * 100) if total_area_proj else 0
    coverings_percentage_proj = (coverings_total_proj / total_area_proj * 100) if total_area_proj else 0
    landscaping_percentage_proj = (landscaping_total_proj / total_area_proj * 100) if total_area_proj else 0
    stone_percentage_proj = (stone_total_proj / total_area_proj * 100) if total_area_proj else 0


    # ------------------------------сбор всего, что есть , с группировкой для упрщен --1кон
    delta_now_proj = total_area_now - total_area_proj

    # --------------- Собранный json для формирования БАЛАНСОВ ----------
    unique_name_objects = list(set(json_now_balance.keys()) | set(json_project_balance.keys()))
    # -----------------создаем словарь, в котром в значении - список
    dict_now_proj = {key: [None, None] for key in unique_name_objects}


    # -------------------Наполняем словарь значениями из сууществующих -------
    for name_obj in unique_name_objects:
        if name_obj in list(set(json_now_balance.keys())):
            # print(dict1.get(name_obj))
            dict_now_proj[name_obj][0] = json_now_balance.get(name_obj)
        else:
            dict_now_proj[name_obj][0] = None

    # -------------------------Наполняем словарь значениями  для проектных

    for name_obj in unique_name_objects:
        if name_obj in list(set(json_project_balance.keys())):
            # print(dict1.get(name_obj))
            dict_now_proj[name_obj][1] = json_project_balance.get(name_obj)
        else:
            dict_now_proj[name_obj][1] = None

    # input_square =  (Project.objects.filter(project_id=project).values('total_square'))
    input_square =  ((Project.objects.filter(id=project.id)
                     .values('total_square'))
                     .first())

    context = {
        'project': project,
        'input_data_now': json_now_balance,
        'input_data_project': json_project_balance,
        'input_data_total': input_data_total,

        # -----------------------------вывод в балансы ---------------
        'json_data_now_and_proj': dict_now_proj,
        # --------------------------Существующ -----------------------
        'json_now_balance': json_now_balance,
        'buildings_total_now': buildings_total_now,
        'coverings_total_now': coverings_total_now,
        'landscaping_total_now': landscaping_total_now,
        'stone_total_now': stone_total_now,

        'buildings_percentage_now': buildings_percentage_now,
        'coverings_percentage_now': coverings_percentage_now,
        'landscaping_percentage_now': landscaping_percentage_now,
        'stone_percentage_now': stone_percentage_now,

        'total_area_now': total_area_now,

        # --------------------------Проектн -----------------------
        'json_project_balance':json_project_balance,
        'buildings_total_proj':buildings_total_proj,
        'coverings_total_proj':coverings_total_proj,
        'landscaping_total_proj':landscaping_total_proj,
        'stone_total_proj':stone_total_proj,

        'buildings_percentage_proj':buildings_percentage_proj,
        'coverings_percentage_proj':coverings_percentage_proj,
        'landscaping_percentage_proj':landscaping_percentage_proj,
        'stone_percentage_proj':stone_percentage_proj,

        'total_area_proj':total_area_proj,
        'delta_now_proj':delta_now_proj,
        'input_square':input_square,


    }
    return render(request, 'results_balance.html', context)
    # return render(request, 'res_1.html', context)


# --------------------------------------------------------------- Демонтаж ------------------------------------------
@login_required
def results_demontaj_view(request, project_id):
    # Добавляем проверку, что проект принадлежит пользователю
    project = get_object_or_404(Project, pk=project_id, user=request.user)

    # --------------------- Демонтаж ---------------
    demontaj_filter = Q(project_id=project) & (Q(event='демонтаж') | Q(event='ремонт')) & (Q(element_id__name_element='Покрытия') | Q(element_id__name_element='Бортовой камень'))
    demontaj_total = (InputData.objects
                      .filter(demontaj_filter)
                      .values('element_id__name_element', 'property_id__property_name', 'event')
                      .annotate(
                          total_square=Coalesce(Sum('square', default=0.0), Value(0.0, output_field=FloatField())),
                          total_length=Coalesce(Sum('length', default=0.0), Value(0.0, output_field=FloatField())),
                      ).order_by('element_id__name_element', 'property_id__property_name'))

    # Группируем данные по категориям (замена defaultdict)
    categories_dict = {}
    counter = 1

    for item in demontaj_total:
        category_name = item['element_id__name_element']
        # # Создаем запись для категории, если ее еще нет
        if category_name not in categories_dict:
            categories_dict[category_name] = []

        # Добавляем элемент в категорию (только площадь, без длины)
        item_data = {
            'number': str(counter),
            # 'name': f"{category_name} - {item['property_id__property_name']}",
            'name': f"{item['property_id__property_name']}",
            'area': f"{item['total_square']:.1f}",
            'note': item['event']
        }
        categories_dict[category_name].append(item_data)
        counter += 1

    # Преобразуем в структуру для шаблона
    categories = [{'name': name, 'items': items} for name, items in categories_dict.items()]

    context = {
        'project': project,
        'categories':categories,
    }
    return render(request, 'results_demontaj.html', context)



@login_required
def results_trotuar_view(request, project_id):
    """Ведомость тротуаров"""
    project = get_object_or_404(Project, pk=project_id, user=request.user)

    # --------------------- Тротуары и площадки ---------------
    trotuar_filter =    (
                           Q(project_id=project)
                        & (Q(event='устройство') | Q(event='ремонт') | Q(event='установка') | Q(event='сохранение')  )
                        & (Q(element_id__name_element='Покрытия') | Q(element_id__name_element='Бортовой камень'))
                        )

    trotuar_dorojki_total = (InputData.objects
                             .filter(trotuar_filter)
                             .values('element_id__name_element', 'property_id__property_name', 'event')
                             .annotate(
                                 total_square=Coalesce(Sum('square', default=0.0), Value(0.0, output_field=FloatField())),
                                 total_length=Coalesce(Sum('length', default=0.0), Value(0.0, output_field=FloatField())),
                             ).order_by('element_id__name_element', 'property_id__property_name'))

    # Группируем данные по категориям (замена defaultdict)
    categories_dict = {}
    counter = 1

    for item in trotuar_dorojki_total:
        category_name = item['element_id__name_element']
        # # Создаем запись для категории, если ее еще нет
        if category_name not in categories_dict:
            categories_dict[category_name] = []

        # Добавляем элемент в категорию (только площадь, без длины)
        item_data = {
            'number': str(counter),
            # 'name': f"{category_name} - {item['property_id__property_name']}",
            'name': f"{item['property_id__property_name']}",
            'area': f"{item['total_square']:.1f}",
            'note': item['event']
        }
        categories_dict[category_name].append(item_data)
        counter += 1

    # Преобразуем в структуру для шаблона
    categories = [{'name': name, 'items': items} for name, items in categories_dict.items()]

    context = {
        'project': project,
        'categories':categories,
    }

    context = {
        'project': project,
        # 'trotuar_dorojki_total': trotuar_dorojki_total,
        # 'trotuar_filter': trotuar_filter,
        'categories': categories,
        # ... другие переменные для тротуаров
    }
    return render(request, 'results_trotuar.html', context)


@login_required
def results_gazon_view(request, project_id):
    """Ведомость газонов"""
    # Добавляем проверку, что проект принадлежит пользователю
    project = get_object_or_404(Project, pk=project_id, user=request.user)

    # -------------------Суммируем по Группам -----------------
    input_data_total = (InputData.objects
                        .filter(project_id=project)
                        .values('element_id__name_element', 'property_id__property_name', 'event')
                        .annotate(
        total_square=Sum('square'),
        total_length=Sum('length')
    ).order_by('element_id__name_element', 'property_id__property_name'))
    input_data_total = calculate_totals(input_data_total)

    # ------------Озеленения -----------------
    total_zelenl = (InputData.objects.filter(project_id=project, element_id__name_element='Озеленение (обводнение)')
                    .values('property_id__property_name', 'event')
                    .annotate(total_square=Sum('square'))
                    .order_by('property_id__property_name'))

    destroyed_properties = []
    for item in total_zelenl:
        destroyed_properties.append(item['property_id__property_name'])

    for item in total_zelenl:
        property_name = item['property_id__property_name']
        if property_name in destroyed_properties:
            item['mark_of_destroy'] = -1
        else:
            item['mark_of_destroy'] = 0

    # Вычисляем суммы для озеленения
    zelen_summ_dict = calcilate_zelen_summ(total_zelenl)  # Сохраняем результат функции в переменную

    # Дополнительно вычисляем количество валидных строк для каждого свойства
    property_valid_counts = {}
    for item in total_zelenl:
        prop_name = item['property_id__property_name']
        if prop_name not in property_valid_counts:
            property_valid_counts[prop_name] = 0

        # Считаем только устройство, сохранение, восстановление
        if item['event'] in ['устройство', 'сохранение', 'восстановление']:
            property_valid_counts[prop_name] += 1

    # Создаем список свойств с дополнительной информацией
    properties_with_counts = []

    # Получаем уникальные названия свойств
    unique_properties = total_zelenl.values('property_id__property_name').distinct()

    for property_group in unique_properties:
        prop_name = property_group['property_id__property_name']

        # Фильтруем элементы для текущего свойства
        property_items = [item for item in total_zelenl if item['property_id__property_name'] == prop_name]

        properties_with_counts.append({
            'name': prop_name,
            'items': property_items,
            'valid_count': property_valid_counts.get(prop_name, 0),
            'sum_value': zelen_summ_dict.get(prop_name, 0)  # Используем словарь, а не функцию
        })

    context = {
        'project': project,
        'input_data_total': input_data_total,
        'total_zelenl': total_zelenl,
        'result_list': destroyed_properties,
        'calcilate_zelen_summ': zelen_summ_dict,  # Передаем словарь, а не функцию
        'properties_with_counts': properties_with_counts,
    }
    return render(request, 'results_gazon.html', context)


@login_required
def v_edit_all_input_data(request, project_id):
    project = get_object_or_404(Project, pk=project_id, user=request.user)

    # ----------------- представление для перехода таб со ВСЕМИ веденными данными --
    # ----------------- для их дальнейшей корректировки -----------------------------

    # input_data = InputData.objects.filter(project_id=project_id).all()

    input_data = (InputData.objects
                  .filter(project_id=project)
                  # .select_related('element_id', 'property_id')
                  .order_by('element_id__name_element', 'property_id__property_name'))




    context = {
                'project': project,
                'input_data': input_data,
             }

    return render(request, 'all_datatab_for_edit.html', context)

@login_required
def edit_input_data(request, pk):
    input_data = get_object_or_404(InputData, pk=pk)

    if request.method == 'POST':
        # Обрабатываем данные формы вручную
        # element_id = request.POST.get('element_id')
        # property_id = request.POST.get('property_id')
        square = request.POST.get('square')
        length = request.POST.get('length')
        event = request.POST.get('event')

        # Обновляем объект
        # input_data.element_id_id = element_id
        # input_data.property_id_id = property_id
        input_data.square = float(square) if square else None
        input_data.length = float(length) if length else None
        input_data.event = event

        input_data.save()
        return redirect('app_calc:results_balance_view', project_id=input_data.project_id.id)

    # Получаем все возможные choices для события
    # event_choices = InputData.EVENT_CHOICES
    event_choices_squ_zis = [('сохранение', 'Сохранение'),
                     ('демонтаж', 'Демонтаж'),
                     ('ремонт', 'Ремонт'),
                     ('устройство', 'Устройство'),
                            ]

    event_choices_ozelen = [('сохранение', 'Сохранение'),
                          # ('ремонт', 'Ремонт'),
                         ('устройство', 'Устройство'),
                         # ('установка', 'Установка'),
                         ('уничтожение', 'Уничтожение'),
                         ('восстановление', 'Восстановление')]
    event_choices_stone = [('сохранение', 'Сохранение'),
                     ('демонтаж', 'Демонтаж'),
                     ('установка', 'Установка'),
                          ]

    marker = 1


    return render(request, 'edit_input_data.html', {
        'input_data': input_data,
        'event_choices_squ_zis': event_choices_squ_zis,
        'event_choices_ozelen': event_choices_ozelen,
        'event_choices_stone': event_choices_stone,

    })

@login_required
def confirm_delete_input_data(request, pk):
    """Страница подтверждения удаления"""
    input_data = get_object_or_404(InputData, pk=pk)
    return render(request, 'confirm_delete.html', {
        'input_data': input_data
    })

@login_required
def delete_input_data(request, pk):
    """Непосредственное удаление"""
    input_data = get_object_or_404(InputData, pk=pk)
    project_id = input_data.project_id.id

    try:
        input_data.delete()
        messages.success(request, 'Запись успешно удалена!')
    except Exception as e:
        messages.error(request, f'Ошибка при удалении: {str(e)}')

    return redirect('app_calc:results_balance_view', project_id=project_id)

@login_required
def edit_balance_data(request, project_id):
    """Редактирование всех записей по выбранной характеристике из баланса"""
    project = get_object_or_404(Project, pk=project_id, user=request.user)

    # Получаем параметры из GET запроса
    element_name = request.GET.get('element')
    property_name = request.GET.get('property')

    if not all([element_name, property_name]):
        messages.error(request, 'Не указаны элемент или характеристика для редактирования')
        return redirect('app_calc:results_balance_view', project_id=project.id)

    try:
        element = Element.objects.get(name_element=element_name)
        property_obj = Property.objects.get(
            element_id=element,
            property_name=property_name
        )

        # Получаем ВСЕ записи InputData для этой характеристики
        input_data_records = InputData.objects.filter(
            project_id=project,
            element_id=element,
            property_id=property_obj
        ).order_by('event')

        if request.method == 'POST':
            # Обрабатываем массовое сохранение
            updated_count = 0
            for record in input_data_records:
                square_key = f"square_{record.id}"
                length_key = f"length_{record.id}"
                event_key = f"event_{record.id}"

                square_value = request.POST.get(square_key)
                length_value = request.POST.get(length_key)
                event_value = request.POST.get(event_key)

                # Обновляем запись если есть изменения
                if square_value is not None:
                    record.square = float(square_value) if square_value else None
                if length_value is not None:
                    record.length = float(length_value) if length_value else None
                if event_value:
                    record.event = event_value

                record.save()
                updated_count += 1

            messages.success(request, f'Успешно обновлено {updated_count} записей!')
            return redirect('app_calc:results_balance_view', project_id=project.id)

        # Если записей нет, создаем базовые записи
        if not input_data_records.exists():
            # Создаем записи для существующего и проектного положений
            base_events = ['сохранение', 'устройство']  # можно добавить другие события по умолчанию
            for event in base_events:
                InputData.objects.create(
                    project_id=project,
                    element_id=element,
                    property_id=property_obj,
                    square=0,
                    length=0,
                    event=event
                )
            input_data_records = InputData.objects.filter(
                project_id=project,
                element_id=element,
                property_id=property_obj
            ).order_by('event')

        # Получаем все возможные choices для событий
        event_choices = InputData.EVENT_CHOICES

        context = {
            'project': project,
            'element': element,
            'property': property_obj,
            'input_data_records': input_data_records,
            'event_choices': event_choices,
        }

        return render(request, 'edit_balance_data.html', context)

    except (Element.DoesNotExist, Property.DoesNotExist) as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('app_calc:results_balance_view', project_id=project.id)


@login_required
def v_edit_demon_data(request, project_id):
    """Редактирование записей демонтажа"""
    project = get_object_or_404(Project, pk=project_id, user=request.user)

    # Получаем параметры из GET запроса
    element_name = request.GET.get('element')
    property_name = request.GET.get('property')

    if not all([element_name, property_name]):
        messages.error(request, 'Не указаны элемент или характеристика для редактирования')
        return redirect('app_calc:results_demontaj_view', project_id=project.id)

    try:
        element = Element.objects.get(name_element=element_name)
        property_obj = Property.objects.get(
            element_id=element,
            property_name=property_name
        )

        # Получаем ВСЕ записи InputData для демонтажа этой характеристики
        input_data_records = InputData.objects.filter(
            project_id=project,
            element_id=element,
            property_id=property_obj
        ).filter(event__in=['демонтаж', 'ремонт']).order_by('event')

        if request.method == 'POST':
            # Обрабатываем массовое сохранение
            updated_count = 0
            for record in input_data_records:
                square_key = f"square_{record.id}"
                length_key = f"length_{record.id}"
                event_key = f"event_{record.id}"

                square_value = request.POST.get(square_key)
                length_value = request.POST.get(length_key)
                event_value = request.POST.get(event_key)

                # Обновляем запись если есть изменения
                if square_value is not None:
                    record.square = float(square_value) if square_value else None
                if length_value is not None:
                    record.length = float(length_value) if length_value else None
                if event_value:
                    record.event = event_value

                record.save()
                updated_count += 1

            messages.success(request, f'Успешно обновлено {updated_count} записей демонтажа!')
            return redirect('app_calc:results_demontaj_view', project_id=project.id)

        # Если записей нет, создаем базовые записи для демонтажа
        if not input_data_records.exists():
            # Создаем записи для демонтажа
            demon_events = ['демонтаж', 'ремонт']
            for event in demon_events:
                InputData.objects.create(
                    project_id=project,
                    element_id=element,
                    property_id=property_obj,
                    square=0,
                    length=0,
                    event=event
                )
            input_data_records = InputData.objects.filter(
                project_id=project,
                element_id=element,
                property_id=property_obj
            ).filter(event__in=['демонтаж', 'ремонт']).order_by('event')

        # Получаем choices для демонтажа
        event_choices_demon = [
            ('демонтаж', 'Демонтаж'),
            ('ремонт', 'Ремонт'),
        ]

        context = {
            'project': project,
            'element': element,
            'property': property_obj,
            'input_data_records': input_data_records,
            'event_choices': event_choices_demon,
        }

        return render(request, 'edit_demon_data.html', context)

    except (Element.DoesNotExist, Property.DoesNotExist) as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('app_calc:results_demontaj_view', project_id=project.id)


@login_required
def v_edit_trotuar_data(request, project_id):
    """Редактирование записей тротуаров и дорожек"""
    project = get_object_or_404(Project, pk=project_id, user=request.user)

    # Получаем параметры из GET запроса
    element_name = request.GET.get('element')
    property_name = request.GET.get('property')

    if not all([element_name, property_name]):
        messages.error(request, 'Не указаны элемент или характеристика для редактирования')
        return redirect('app_calc:results_trotuar_view', project_id=project.id)

    try:
        element = Element.objects.get(name_element=element_name)
        property_obj = Property.objects.get(
            element_id=element,
            property_name=property_name
        )

        # Получаем ВСЕ записи InputData для тротуаров этой характеристики
        input_data_records = InputData.objects.filter(
            project_id=project,
            element_id=element,
            property_id=property_obj
        ).filter(event__in=['устройство', 'ремонт', 'установка', 'сохранение']).order_by('event')

        if request.method == 'POST':
            # Обрабатываем массовое сохранение
            updated_count = 0
            for record in input_data_records:
                square_key = f"square_{record.id}"
                length_key = f"length_{record.id}"
                event_key = f"event_{record.id}"

                square_value = request.POST.get(square_key)
                length_value = request.POST.get(length_key)
                event_value = request.POST.get(event_key)

                # Обновляем запись если есть изменения
                if square_value is not None:
                    record.square = float(square_value) if square_value else None
                if length_value is not None:
                    record.length = float(length_value) if length_value else None
                if event_value:
                    record.event = event_value

                record.save()
                updated_count += 1

            messages.success(request, f'Успешно обновлено {updated_count} записей тротуаров!')
            return redirect('app_calc:results_trotuar_view', project_id=project.id)

        # Если записей нет, создаем базовые записи для тротуаров
        if not input_data_records.exists():
            # Создаем записи для тротуаров
            trotuar_events = ['устройство', 'ремонт', 'сохранение']
            for event in trotuar_events:
                InputData.objects.create(
                    project_id=project,
                    element_id=element,
                    property_id=property_obj,
                    square=0,
                    length=0,
                    event=event
                )
            input_data_records = InputData.objects.filter(
                project_id=project,
                element_id=element,
                property_id=property_obj
            ).filter(event__in=['устройство', 'ремонт', 'установка', 'сохранение']).order_by('event')

        # Получаем choices для тротуаров
        event_choices_trotuar = [
            ('устройство', 'Устройство'),
            ('ремонт', 'Ремонт'),
            ('установка', 'Установка'),
            ('сохранение', 'Сохранение'),
        ]

        context = {
            'project': project,
            'element': element,
            'property': property_obj,
            'input_data_records': input_data_records,
            'event_choices': event_choices_trotuar,
        }

        return render(request, 'edit_trotuar_data.html', context)

    except (Element.DoesNotExist, Property.DoesNotExist) as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('app_calc:results_trotuar_view', project_id=project.id)


@login_required
def v_edit_gazon_data(request, project_id):
    """Редактирование записей газонов и озеленения"""
    project = get_object_or_404(Project, pk=project_id, user=request.user)

    # Получаем параметры из GET запроса
    element_name = request.GET.get('element')
    property_name = request.GET.get('property')

    if not all([element_name, property_name]):
        messages.error(request, 'Не указаны элемент или характеристика для редактирования')
        return redirect('app_calc:results_gazon_view', project_id=project.id)

    try:
        element = Element.objects.get(name_element=element_name)
        property_obj = Property.objects.get(
            element_id=element,
            property_name=property_name
        )

        # Получаем ВСЕ записи InputData для озеленения этой характеристики
        input_data_records = InputData.objects.filter(
            project_id=project,
            element_id=element,
            property_id=property_obj
        ).filter(event__in=['уничтожение', 'устройство', 'сохранение', 'восстановление']).order_by('event')

        if request.method == 'POST':
            # Обрабатываем массовое сохранение
            updated_count = 0
            for record in input_data_records:
                square_key = f"square_{record.id}"
                event_key = f"event_{record.id}"

                square_value = request.POST.get(square_key)
                event_value = request.POST.get(event_key)

                # Обновляем запись если есть изменения
                if square_value is not None:
                    record.square = float(square_value) if square_value else None
                if event_value:
                    record.event = event_value

                record.save()
                updated_count += 1

            messages.success(request, f'Успешно обновлено {updated_count} записей озеленения!')
            return redirect('app_calc:results_gazon_view', project_id=project.id)

        # Если записей нет, создаем базовые записи для озеленения
        if not input_data_records.exists():
            # Создаем записи для озеленения
            gazon_events = ['уничтожение', 'устройство', 'сохранение', 'восстановление']
            for event in gazon_events:
                InputData.objects.create(
                    project_id=project,
                    element_id=element,
                    property_id=property_obj,
                    square=0,
                    length=0,
                    event=event
                )
            input_data_records = InputData.objects.filter(
                project_id=project,
                element_id=element,
                property_id=property_obj
            ).filter(event__in=['уничтожение', 'устройство', 'сохранение', 'восстановление']).order_by('event')

        # Получаем choices для озеленения
        event_choices_gazon = [
            ('уничтожение', 'Уничтожение'),
            ('устройство', 'Устройство'),
            ('сохранение', 'Сохранение'),
            ('восстановление', 'Восстановление'),
        ]

        # Вычисляем сумму для устройства, сохранения и восстановления
        sum_value = sum([
            record.square for record in input_data_records
            if record.event in ['устройство', 'сохранение', 'восстановление'] and record.square
        ])

        context = {
            'project': project,
            'element': element,
            'property': property_obj,
            'input_data_records': input_data_records,
            'event_choices': event_choices_gazon,
            'sum_value': sum_value,
        }

        return render(request, 'edit_gazon_data.html', context)

    except (Element.DoesNotExist, Property.DoesNotExist) as e:
        messages.error(request, f'Ошибка: {str(e)}')
        return redirect('app_calc:results_gazon_view', project_id=project.id)