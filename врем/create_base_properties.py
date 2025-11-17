import os
import django
import sys

# Добавьте путь к вашему проекту
sys.path.append('C:/Users/TurchinMV/PycharmProjects/blago_tab')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blago_tab.settings')
django.setup()

from app_calc.models import Element, Property


def create_base_properties():
    base_properties = {
        'Покрытия': ['асфальтобетон (проезд)',
                     'асфальтобетон (тротуар)',
                     'цементобетонное покрытие',
                     'бетонная плитка',
                     'гранитная плитка',
                     'щебеночное покрытие',
                     'гранитный отсев',
                     'TerraWay',
                     'резиновое покрытие',
                     'песчаное покрытие',
                     'искусственный газон',
                     'древесная кора',
                     'гранитная брусчатка',
                     ],

        'Бортовой камень': ['Бортовой камень бетонный 150',
                            'Бортовой камень бетонный 180',
                            'Бортовой камень гранитный 150',
                            'Бортовой камень гранитный 200',
                            'Бортовой камень гранитный 300',
                            'Пандус гранитный 150',
                            'Угловой элемент гранитный 150', ],
        'Озеленение (обводнение)': ['цветники',
                                    'газон/травяной покров',
                                    'мульча',
                                    'водная поверхность', ],
        'Здания и сооружения': ['здания/сооружения',
                                'лестницы',
                                'пандусы',
                                'подпорные стенки',
                                ]
    }

    for element_name, properties in base_properties.items():
        element, created = Element.objects.get_or_create(name_element=element_name)
        print(f"Element: {element_name} - {'created' if created else 'exists'}")

        for prop_name in properties:
            prop, created = Property.objects.get_or_create(
                element_id=element,
                property_name=prop_name,
                defaults={'project': None}  # Базовые характеристики без привязки к проекту
            )
            print(f"  Property: {prop_name} - {'created' if created else 'exists'}")

    print("Base properties creation completed!")


if __name__ == '__main__':
    create_base_properties()