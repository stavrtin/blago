from django.conf.urls import handler404

from django.conf import settings
from django.conf.urls.static import static


from django.urls import path
from .views_calc import tab_start_view
from .views_calc import results_view
from .views_calc import get_properties
from .views_calc import projects_list_view
from .views_calc import new_proj_view
from .views_calc import v_edit_all_input_data
from .views_calc import edit_input_data, delete_input_data, confirm_delete_input_data


app_name = 'app_calc'  # Убедитесь, что это указано


urlpatterns = [

    # path('', tab_start_view, name='tab_start_view'),
    path('tab_start_view/<int:project_id>/', tab_start_view, name='tab_start_view'),
    path('new_proj_view/', new_proj_view, name='new_proj_view'),
    # path('results/', results_view, name='results_view'),
    # path('api/properties/', get_properties, name='get_properties'),
    #     ------- logout-----
    # path('', login_view, name='login'),
    # path('logout', logout, name='logout'),
    path('', projects_list_view, name='projects_list'),
    path('project/<int:project_id>/', tab_start_view, name='tab_start_view'),
    path('project/<int:project_id>/results/', results_view, name='results_view'),
    path('api/properties/', get_properties, name='get_properties'),
    path('edit_all_input_data/<int:project_id>', v_edit_all_input_data, name='v_edit_all_input_data'),
    path('input-data/<int:pk>/edit/', edit_input_data, name='edit_input_data'),
    path('input-data/<int:pk>/delete/', delete_input_data, name='delete_input_data'),
    path('input-data/<int:pk>/confirm-delete/', confirm_delete_input_data, name='confirm_delete_input_data'),


    path('help', help, name='help'),



]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Устанавливаем обработчик для 404 ошибок
# handler404 = custom_404_view

