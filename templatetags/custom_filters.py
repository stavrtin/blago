# В файле templatetags/custom_filters.py
from django import template

register = template.Library()

@register.filter
def sum_by_event(items, event):
    """Суммирует площадь для определенного события"""
    return sum(item.total_square for item in items if item.event == event)

@register.filter
def filter_by_event(items, event):
    """Фильтрует элементы по событию"""
    return [item for item in items if item.event == event]