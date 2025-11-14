from django.urls import path
from .views_calc import (
    tab_start_view, results_view, get_properties,
    projects_list_view, new_proj_view, v_edit_all_input_data,
    edit_input_data, delete_input_data, confirm_delete_input_data,
    start_login_view, start_register_view, logout_view,  # Добавляем новые представления
    results_balance_view,
    results_demontaj_view,
    results_gazon_view,
    results_trotuar_view,
# edit_balance_data, ---------------
edit_balance_data,
v_edit_demon_data,
v_edit_trotuar_data,
v_edit_gazon_data,
add_new_property,
)

app_name = 'app_calc'

urlpatterns = [
    path('', start_login_view, name='start_login'),
    path('register/', start_register_view, name='start_register'),
    path('logout/', logout_view, name='logout'),
    path('projects/', projects_list_view, name='projects_list'),
    path('tab_start_view/<int:project_id>/', tab_start_view, name='tab_start_view'),
    path('new_proj_view/', new_proj_view, name='new_proj_view'),
    path('project/<int:project_id>/results/', results_view, name='results_balance_view'),
    path('api/properties/', get_properties, name='get_properties'),
    path('edit_all_input_data/<int:project_id>', v_edit_all_input_data, name='v_edit_all_input_data'),
    path('input-data/<int:pk>/edit/', edit_input_data, name='edit_input_data'),
    path('input-data/<int:pk>/delete/', delete_input_data, name='delete_input_data'),
    path('input-data/<int:pk>/confirm-delete/', confirm_delete_input_data, name='confirm_delete_input_data'),
    path('project/<int:project_id>/balance/', results_balance_view, name='results_balance_view'),
    path('project/<int:project_id>/demontaj/', results_demontaj_view, name='results_demontaj_view'),
    path('project/<int:project_id>/gazon/', results_gazon_view, name='results_gazon_view'),
    path('project/<int:project_id>/trotuar/', results_trotuar_view, name='results_trotuar_view'),
# path('project/<int:project_id>/edit-balance/', edit_balance_data, name='edit_balance_data'),
#     ------------------- правки балансов --------------------
path('project/<int:project_id>/edit-from-balance/', edit_balance_data, name='edit_balance_data'),
path('project/<int:project_id>/edit-demon-data/', v_edit_demon_data, name='v_edit_demon_data'),
path('project/<int:project_id>/edit-trotuar-data/', v_edit_trotuar_data, name='v_edit_trotuar_data'),
path('project/<int:project_id>/edit-gazon-data/', v_edit_gazon_data, name='v_edit_gazon_data'),
# ------------------------ новые характеристики -------
path('project/<int:project_id>/add-property/', add_new_property, name='add_new_property'),
path('get_properties/', get_properties, name='get_properties'),


]
