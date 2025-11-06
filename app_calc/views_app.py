from django.shortcuts import render, get_object_or_404, redirect
from .models import BusinessCard
from django.db import connection
from django.core.paginator import Paginator
from django import forms
import datetime
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse, reverse_lazy
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group

# import openpyxl
# from io import BytesIO
# from openpyxl.styles import PatternFill, Alignment, Font, Border, Side
import json

from django.http import HttpResponse

import pytesseract
from PIL import Image
import re

import logging
from logging.handlers import RotatingFileHandler
import httpx

import subprocess

#Логирование
# Настройка логирования в файл
file_handler = RotatingFileHandler(
    filename='app_viz/logs/app.log',
    maxBytes=5*1024*1024,    # 5 МБ на файл
    backupCount=30,           # хранить три старых файла
    encoding='utf-8'
)
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

file_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

import pytesseract
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\TurchinMV\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# MODEL_API_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_API_URL = "http://localhost:11434/api/chat"

chat_history = []



def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            print(f"-----------------------------------------------------User {user} вошел")
            return redirect('app_viz:v_home')
            # return redirect('start_page')
        else:
            error_message = "Вас нет в списке"
            return render(request, 'login.html', {'error_message': error_message})

    return render(request, 'login.html')





def logout(request):
    auth_logout(request)  # Выход из аккаунта
    print("-----------------------------------------00-----User logged out")  # Отладочное сообщение
    return redirect('login')  # Перенаправление на главную страницу


def start_page(request):
    # -------------- получаю принадлежность к группе -------
    user_groups_list = []
    for i in request.user.groups.all():
        print(i)
        user_groups_list.append(str(i))

    return render(request, 'home_3.html',
                         {
                      'groups': user_groups_list,
                         }              )

def v_finde(request):
    # -------------- получаю принадлежность к группе -------
    user_groups_list = []
    for i in request.user.groups.all():
        print(i)
        user_groups_list.append(str(i))


    return render(request, 'finde_page.html',
                         {
                      'groups': user_groups_list,
                         }              )

@login_required
def v_home(request):
    # --------------
    user_groups_list = []
    for i in request.user.groups.all():
        print(i)
        user_groups_list.append(str(i))
    # --------------

    # # is_vps_group = request.user.groups.filter(name='vps').exists()
    query_fio = request.GET.get('search_name', '')  # Получаем строку поиска по FIO
    query_company = request.GET.get('search_company', '')  # Получаем строку поиска по курирующему подразделению
    query_position = request.GET.get('search_position', '')  # Получаем строку поиска по курирующему подразделению
    query_helper = request.GET.get('search_helper', '')  # Получаем строку поиска по курирующему подразделению
    # query_otrabot = request.GET.get('search_otrabot', '')  # Получаем строку поиска по отработанным записям
    # query_data_vizova_smp = request.GET.get('search_data_vizova_smp', '')  # Получаем строку поиска по дате смп

    records_per_page = request.GET.get('records_per_page', 20)  # Получаем количество записей на странице


    print(f'-----------{query_fio}')


    # Обработка фильтров из GET-запроса
    if request.method == 'GET':
        if 'records_per_page' in request.GET and request.GET['records_per_page'] != '':
            request.session['records_per_page'] = int(request.GET['records_per_page'])
        records_per_page = request.GET.get('records_per_page', request.session.get('records_per_page', 20))

        if 'search_name' in request.GET:
            query_fio = request.GET.get('search_name', '')

        if 'search_company' in request.GET:
            query_company = request.GET.get('search_company', '')

        if 'search_position' in request.GET:
            query_position = request.GET.get('search_position', '')

        if 'search_helper' in request.GET:
            query_helper = request.GET.get('search_helper', '')


    # Фильтруем данные по обоим полям и сортируем по p_p
    data_smp = BusinessCard.objects.filter(activate=True).order_by('name')  # Сортировка по возрастанию p_p
    # Фильтруем данные по обоим полям
    # if user_groups_list == ['vps']:
    #     # Исключаем записи, у которых ok_vps равно "ВПС"
    #     data_smp = BusinessCard.objects.filter(ok_vps="впс").order_by('data_vyzova_smp',
    #                                                                               'fio_pacienta')  # Сортировка по возрастанию
    # else:
    #     data_smp = BusinessCard.objects.all().order_by('data_vyzova_smp', 'fio_pacienta')  # Сортировка по возрастанию

    total_records = data_smp.count()  # Общее количество записей

    if query_fio:
        # data_smp = data_smp.filter(name__icontains=query_fio)
        data_smp = data_smp.filter(name__icontains=query_fio)

    if query_company:
        data_smp = data_smp.filter(company__icontains=query_company)

    if query_position:
        data_smp = data_smp.filter(position__icontains=query_position)

    if query_helper:
       data_smp = data_smp.filter(helper__icontains=query_helper)



    # Получаем уникальные значения для выпадающего списка
    # unique_kurir = BusinessCard.objects.values_list('kuriruyushchee_podrazdelenie_ovpp', flat=True).distinct()
    # unique_otrab = BusinessCard.objects.values_list('ok_vps', flat=True).distinct()

    paginator = Paginator(data_smp, records_per_page)  # Показывать 10 записей на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    filter_records = data_smp.count()  #  количество записей - отфильтрованное

    return render(request, 'home_3.html', {
    # return render(request, 'home.html', {
        'data_smp': page_obj,
        'paginator': paginator,
        # 'page_obj': page_obj,
        'search_name': query_fio,
        'search_company': query_company,
        'search_position': query_position,
        'search_helper': query_helper,
        # 'search_otrabot': query_otrabot,
        # 'search_data_vizova_smp': query_data_vizova_smp,

        'records_per_page': records_per_page,
        'total_records': total_records,  # Передаем общее количество записей
        # 'unique_kurir': unique_kurir,  # Передаем уникальные значения в контекст по курир. филиалу ВПС
        # 'unique_otrab': unique_otrab,  # Передаем уникальные значения в контекст по отработанным в КЭР
        'groups': user_groups_list, # Получаем все группы
        'filter_records': filter_records,  #  количество записей - отфильтрованное
    })

@login_required
def v_new_card(request):
    if request.method == 'POST':
        print('-----------------тест вывода1 ------------')
        business_card = BusinessCard(
            name=request.POST['name'],
            company=request.POST.get('company'),
            position=request.POST.get('position'),

            point_meet=request.POST.get('point_meet'),
            helper=request.POST.get('helper'),

            phone=request.POST.get('phone'),
            email=request.POST.get('email'),
            address=request.POST.get('address'),
            website=request.POST.get('website'),

            photo=request.FILES.get('photo')  # Получаем загруженное изображение
        )
        business_card.activate = True
        print('-------------с пустым фото сформировала ЗАПИСЬ ---------')
        business_card.save()  # Сохраняем объект в базе данных
        print('-------------сохранение с пустым фото прошло---------')


        if 'cards_save' in request.POST:  # Кнопка "Сохранить"
            print('109-----------------cards_save')
            business_card.save()
            return redirect('app_viz:v_home')

        elif 'cards_parser' in request.POST:  # Кнопка "Распарсить фото"
            print('109-----------------не должно сохранять и на парсинг')
            print(f'{business_card=}')
            print(f'{business_card.photo=}')
            return redirect('app_viz:v_parsing_foto', id=business_card.id)  #  на страницу парсера

    return render(request, 'new_card_1.html')




from django.contrib import messages
@login_required
def v_person_detals(request, id):

    user_groups_list = []
    for i in request.user.groups.all():
        print(i)
        user_groups_list.append(str(i))

    business_card = get_object_or_404(BusinessCard, id=id)  # Получаем запись по ID

    if 'btn_edit' in request.POST:  # Кнопка "Изменить запись"
        # logger.info(f'пользователь {request.user} нажал btn_correct_kriter и зашел в правки по kriter -  {patient.fio_pacienta}')
        #  передам через сессию СТАТУС последний по состоянию заявки
        # request.session['status_last_date'] = status_last_date

        return redirect('app_viz:edit_card', id=business_card.id)

    if 'btn_delete' in request.POST:  # Кнопка "Удалить запись"
        # logger.info(f'пользователь {request.user} нажал btn_correct_kriter и зашел в правки по kriter -  {patient.fio_pacienta}')
        #  передам через сессию СТАТУС последний по состоянию заявки
        # request.session['status_last_date'] = status_last_date

        return redirect('app_viz:delete_card', id=business_card.id)

    # return render(request, 'persone_card.html', {
    # return render(request, 'pers_1.html', {  'business_card': business_card,})
    return render(request, 'pers_2.html', {  'business_card': business_card,})


@login_required
def v_edit_card(request, id):

    user_groups_list = []
    for i in request.user.groups.all():
        print(i, 'ssss-----')
        user_groups_list.append(str(i))

    business_card = get_object_or_404(BusinessCard, id=id)  # Получаем запись по ID

    if request.method == 'POST':
        if 'btn_edit_save' in request.POST:
            # Обновляем поля существующего объекта
            business_card.name = request.POST.get('name')
            business_card.company = request.POST.get('company')
            business_card.position = request.POST.get('position')
            business_card.point_meet = request.POST.get('point_meet')
            business_card.helper = request.POST.get('helper')
            business_card.phone = request.POST.get('phone')
            business_card.email = request.POST.get('email')
            business_card.address = request.POST.get('address')
            business_card.website = request.POST.get('website')
            # business_card.photo = request.FILES['photo']
            # # Для файла (photo) используем request.FILES, а не request.POST!
            if 'photo' in request.FILES:
                business_card.photo = request.FILES['photo']

            business_card.save()  # Сохраняем изменения в существующей записи
            return redirect('app_viz:v_home')

    # return render(request, 'edit_card_0.html', {'business_card': business_card})
    # return render(request, 'edit_card_1.html', {'business_card': business_card})
    return render(request, 'edit_card_2.html', {'business_card': business_card})

@login_required
def v_delete_card(request, id):

    user_groups_list = []
    for i in request.user.groups.all():
        print(i)
        user_groups_list.append(str(i))

    business_card = get_object_or_404(BusinessCard, id=id)  # Получаем запись по ID

    if 'btn_delete' in request.POST:  # Кнопка "Удалить"
        business_card.activate = False
        business_card.save()
        return redirect('app_viz:v_home')  # Переходим на страницу проверки


    # return render(request, 'persone_card.html', {
    return render(request, 'delete_pers_0.html', {
                                                    'business_card': business_card,
                                                    # 'all_oborudovanie': all_oborudovanie,
                                                            })

@login_required
def v_parsing_foto(request, id):
# def v_parsing_foto(request):
    # ---- тут собираем данные с визитки -----------
    client = get_object_or_404(BusinessCard, id=id)
    print(f'-------------111{client.photo=}')
    file_name = client.photo

    # Очищаем сессию после использования
    if 'unsaved_card_data' in request.session:
        del request.session['unsaved_card_data']

    # ------------- механизм чтения ---------------
    text = pytesseract.image_to_string(Image.open(file_name), lang="rus+eng")

    print(text)
    # text_from_foto = (parse_business_card(text))
    text_from_model = (send_model_message(text))

    print(f'--------------------{text_from_model=}')

    # ------------------- проверка работоспособности модели ----------
    if text_from_model:
        # --------- изменю ключи в словаре (для правильного вывода в шаблон) --
        text_from_model["фио"] = text_from_model.pop("Фамилия имя отчество")
        text_from_model["место_работы"] = text_from_model.pop("Место работы")

        # -------------- уберем запятые в ФИО --------------------
        text_from_model["фио"] = text_from_model['фио'].replace(',', '')

        # print(f'--v_parsing_foto--{text_from_foto}')

        context = { 'client': client,
                    'client_foto': file_name,
                    'text_from_foto': text,
                    'text_from_model': text_from_model,
                    # 'business_card':business_card,
                  }

        if request.method == 'POST':
            if 'cards_save' in request.POST:
                # Обновляем поля существующего объекта
                client.name = request.POST.get('name')
                client.company = request.POST.get('company')
                client.position = request.POST.get('position')
                client.point_meet = request.POST.get('point_meet')
                client.helper = request.POST.get('helper')
                client.phone = request.POST.get('phone')
                client.email = request.POST.get('email')
                client.address = request.POST.get('address')
                client.website = request.POST.get('website')
                client.activate = True
                # client.photo = request.FILES['photo']
                # # Для файла (photo) используем request.FILES, а не request.POST!
                if 'photo' in request.FILES:
                    client.photo = request.FILES['photo']

                client.save()  # Сохраняем изменения в существующей записи
                return redirect('app_viz:v_home')



                business_card.save()
                return redirect('app_viz:v_home')
    else:
        print('-----------модель не включилась !!--')
        text_from_model =         {
                                "Должность": "Что-то не так с фотографией. Модель не включилась (( ",
                                "Фамилия имя отчество": "",
                                "Место работы": "Попробуйте еще раз перезапустить",
                                "Адрес": "Попробуйте или записать вручную или еще раз перезапустить",
                                "Телефон": "",
                                "Email": "",
                                "Сайт": ""
                            }
        context = {'client': client,
                   'client_foto': file_name,
                   'text_from_foto': text,
                   'text_from_model': text_from_model,
                   # 'business_card':business_card,
                   }

    # Обработка POST запроса (сохранение данных)
    if request.method == 'POST':
        if 'cards_save' in request.POST:
            # Обновляем поля объекта
            client.name = request.POST.get('name', '')
            client.company = request.POST.get('company', '')
            client.position = request.POST.get('position', '')
            client.point_meet = request.POST.get('point_meet', '')
            client.helper = request.POST.get('helper', '')
            client.phone = request.POST.get('phone', '')
            client.email = request.POST.get('email', '')
            client.address = request.POST.get('address', '')
            client.website = request.POST.get('website', '')
            client.activate = True

            # Обработка загруженного фото (если есть)
            if 'photo' in request.FILES:
                client.photo = request.FILES['photo']

            client.save()
            return redirect('app_viz:v_home')

        elif 'cards_cancel' in request.POST:
            # Удаляем карточку при отмене
            client.delete()
            return redirect('app_viz:v_home')

    return render(request, 'new_card_2.html', context)


def send_model_message(user_message):
    """
    Отправляет запрос к модели Ollama для извлечения структурированной информации
    """
    MODEL_API_URL = 'http://localhost:11434/api/chat'
    headers = {"Content-Type": "application/json"}

    # Более детальный системный промпт
    system_prompt = """Ты - ассистент для извлечения структурированной информации из текста. 
    Извлеки информацию и верни ТОЛЬКО JSON в строгом формате:
    {
        "Должность": "",
        "Фамилия имя отчество": "",
        "Место работы": "",
        "Адрес": "",
        "Телефон": "",
        "Email": "",
        "Сайт": ""
    }

    Если информация не найдена, оставь поле пустым. Не добавляй никакого дополнительного текста, только JSON."""

    data = {
        "model": "gemma3:1b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Извлеки информацию из текста: {user_message}"}
        ],
        "temperature": 0.1,
        "top_p": 0.9,
        "stream": False
    }
    try:
        response = httpx.post(
            MODEL_API_URL,
            json=data,
            headers=headers,
            timeout=120.0  # Уменьшил таймаут до 120 секунд
        )
        if response.status_code == 200:
            response_data = response.json()
            # Извлекаем содержимое ответа
            content = response_data['message']['content']

            # Пытаемся найти и распарсить JSON
            try:
                # Ищем JSON в ответе
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_str = content[json_start:json_end]
                    result_json_model = json.loads(json_str)
                    return result_json_model           #-------- ответ модели ---
                else:
                    print(f"JSON не найден в ответе: {content}")
                    return None
            except json.JSONDecodeError as e:
                print(f"Ошибка парсинга JSON: {e}")
                print(f"Ответ модели: {content}")
                return None
        else:
            print(f"Ошибка запроса: {response.status_code}")
            print(f"Ответ сервера: {response.text}")
            return None

    except httpx.RequestError as e:
        print(f"Ошибка подключения: {e}")
        return None
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return None



def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

