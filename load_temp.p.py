import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blago_tab.settings')
django.setup()

from app_calc.models import Element, Property

def load_data():
    print('Loading initial data...')

    elements_data = {
        'Покрытия': [
            'асфальтобетон (проезжая часть)',
            'асфальтобетон (тротуар)',
            'щебеночное покрытие',
            'бетонный лоток',
            'гранитный отсев',
            'бетонная плитка'
        ],
        'Здания и сооружения': [
            'здания_и_сооружения',
            'лестницы',
            'пандусы'
        ],
        'Озеленение_обводнение': [
            'травяной покров',
            'цветники'
        ],
        'Бортовой камень': [
            'Бортовой камень бетонный - 150',
            'Бортовой камень бетонный - 180',
            'Бортовой камень гранитный - 150',
            'Бортовой камень гранитный - 200',
            'Бортовой камень гранитный - 300',
            'Пандус гранитный - 150',
            'Угловой элемент гранитный - 150'
        ]
    }

    for element_name, properties in elements_data.items():
        element, created = Element.objects.get_or_create(name_element=element_name)
        print(f'{"Created" if created else "Exists"} element: {element_name}')

        for property_name in properties:
            prop, created = Property.objects.get_or_create(
                element_id=element,
                property_name=property_name,
                project=None
            )
            print(f'  {"Created" if created else "Exists"} property: {property_name}')

    print('Successfully loaded all initial data!')

if __name__ == '__main__':
    load_data()