from django.urls import path
from .views_calc import (
    tab_start_view, results_view, get_properties,
    projects_list_view, new_proj_view, v_edit_all_input_data,
    edit_input_data, delete_input_data, confirm_delete_input_data,
    start_login_view, start_register_view, logout_view  # Добавляем новые представления
)

app_name = 'app_calc'

urlpatterns = [
    path('', start_login_view, name='start_login'),
    path('register/', start_register_view, name='start_register'),
    path('logout/', logout_view, name='logout'),
    path('projects/', projects_list_view, name='projects_list'),
    path('tab_start_view/<int:project_id>/', tab_start_view, name='tab_start_view'),
    path('new_proj_view/', new_proj_view, name='new_proj_view'),
    path('project/<int:project_id>/results/', results_view, name='results_view'),
    path('api/properties/', get_properties, name='get_properties'),
    path('edit_all_input_data/<int:project_id>', v_edit_all_input_data, name='v_edit_all_input_data'),
    path('input-data/<int:pk>/edit/', edit_input_data, name='edit_input_data'),
    path('input-data/<int:pk>/delete/', delete_input_data, name='delete_input_data'),
    path('input-data/<int:pk>/confirm-delete/', confirm_delete_input_data, name='confirm_delete_input_data'),
]