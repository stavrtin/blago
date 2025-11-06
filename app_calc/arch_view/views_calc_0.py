from django.shortcuts import render, get_object_or_404, redirect
# from .models import BusinessCard
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

from .models import DataFields, InputData

# import openpyxl
# from io import BytesIO
# from openpyxl.styles import PatternFill, Alignment, Font, Border, Side
import json

from django.http import HttpResponse

# import pytesseract
# from PIL import Image
# import re

import logging
from logging.handlers import RotatingFileHandler
# import httpx

import subprocess

#Логирование
#
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            print(f"-----------------------------------------------------User {user} вошел")
            return redirect('app_calc:input_view')
            # return redirect('start_page')
        else:
            error_message = "Вас нет в списке"
            return render(request, 'login.html', {'error_message': error_message})

    return render(request, 'login.html')

def logout(request):
    auth_logout(request)  # Выход из аккаунта
    print("-----------------------------------------00-----User logged out")  # Отладочное сообщение
    return redirect('login')  # Перенаправление на главную страницу


# def input_view(request):
#     if request.method == 'POST':
#         # Обработка данных формы
#         object_name = request.POST.get('object')
#         property_val = request.POST.get('property')
#         square_val = request.POST.get('square')
#         length_val = request.POST.get('length')
#         event_val = request.POST.get('event')
#
#         # Сохранение в базу данных
#         DataFields.objects.create(
#             object=object_name,
#             property=property_val,
#             square=square_val,
#             length=length_val,
#             event=event_val
#         )
#         return redirect('input_view')
#
#     # Пример данных для таблиц (замените на реальные данные из вашей модели)
#     context = {
#         'demolition_data': [],  # Ваши данные для ведомости демонтажа
#         'sidewalk_data': [],  # Ваши данные для ведомости тротуаров
#         'lawn_data': [],  # Ваши данные для ведомости газонов
#         'balance_data': []  # Ваши данные для балансов
#     }
#
#     return render(request, 'results.html', context)


def input_view(request):
    if request.method == 'POST':
        # Обработка данных формы
        object_name = request.POST.get('object')
        property_val = request.POST.get('property')
        square_val = request.POST.get('square')
        length_val = request.POST.get('length')
        event_val = request.POST.get('event')

        # Сохранение в базу данных (если нужно)
        if object_name:  # Проверяем, что объект не пустой
            DataFields.objects.create(
                object=object_name,
                property=property_val,
                square=square_val if square_val else None,
                length=length_val if length_val else None,
                event=event_val
            )

        # Перенаправляем на эту же страницу после отправки формы
        return redirect('input_view')

    # Получаем данные из базы (если нужно)
    objects = DataFields.objects.all()

    # Пример данных для таблиц (замените на реальные данные)
    context = {
        'demolition_data': [
            {'name': 'Объект 1', 'area': '100', 'note': 'Примечание 1'},
            {'name': 'Объект 2', 'area': '200', 'note': 'Примечание 2'},
        ],
        'sidewalk_data': [
            {'name': 'Тротуар 1', 'coating_type': 'Асфальт', 'area': '150', 'note': ''},
            {'name': 'Тротуар 2', 'coating_type': 'Плитка', 'area': '80', 'note': ''},
        ],
        'lawn_data': [
            {'name': 'Газон 1', 'area': '300', 'note': 'Парковый'},
            {'name': 'Газон 2', 'area': '120', 'note': 'Уличный'},
        ],
        'balance_data': [
            {'name': 'Баланс 1', 'existing_area': '1000', 'existing_percent': '25%',
             'project_area': '1200', 'project_percent': '30%'},
            {'name': 'Баланс 2', 'existing_area': '800', 'existing_percent': '20%',
             'project_area': '1000', 'project_percent': '25%'},
        ]
    }

    return render(request, 'results.html', context)


def tab_start_view(request):
    # Обработка POST запроса (добавление новых данных)
    if request.method == 'POST':
        object_name = request.POST.get('object')
        property_val = request.POST.get('property')
        square_val = request.POST.get('square')
        length_val = request.POST.get('length')
        event_val = request.POST.get('event')
        # Валидация значения event
        valid_events = ['сохранение', 'демонтаж', 'ремонт', 'устройство']
        if event_val not in valid_events:
            event_val = None

        # Сохраняем данные в базу
        if object_name:  # Проверяем, что объект не пустой
            InputData.objects.create(
                object=object_name,
                property=property_val if property_val else None,
                square=float(square_val) if square_val else None,
                length=float(length_val) if length_val else None,
                event=event_val if event_val else None
            )

        # Перенаправляем на эту же страницу (очищает форму)
        return redirect('app_calc:tab_start_view')

    # Получаем все данные из базы для таблицы
    input_data = InputData.objects.all()

    context = {
        'input_data': input_data,
        'event_choices': InputData.EVENT_CHOICES  # Передаем choices в шаблон
    }

    return render(request, 'tab_start.html', context)


def results_view(request):
    # Представление для страницы "Итоги" (заглушка)
    input_data = InputData.objects.all()

    context = {
        'input_data': input_data,
        'demolition_data': [
            {'name': 'Объект 1', 'area': '100', 'note': 'Примечание 1'},
            {'name': 'Объект 2', 'area': '200', 'note': 'Примечание 2'},
        ],
        'sidewalk_data': [
            {'name': 'Тротуар 1', 'coating_type': 'Асфальт', 'area': '150', 'note': ''},
            {'name': 'Тротуар 2', 'coating_type': 'Плитка', 'area': '80', 'note': ''},
        ],
        'lawn_data': [
            {'name': 'Газон 1', 'area': '300', 'note': 'Парковый'},
            {'name': 'Газон 2', 'area': '120', 'note': 'Уличный'},
        ],
        'balance_data': [
            {'name': 'Баланс 1', 'existing_area': '1000', 'existing_percent': '25%',
             'project_area': '1200', 'project_percent': '30%'},
            {'name': 'Баланс 2', 'existing_area': '800', 'existing_percent': '20%',
             'project_area': '1000', 'project_percent': '25%'},
        ]
    }

    return render(request, 'results_1.html', context)


def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

