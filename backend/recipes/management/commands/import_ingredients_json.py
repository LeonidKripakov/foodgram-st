import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из JSON-файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            help='Путь к JSON-файлу с ингредиентами'
        )

    def handle(self, *args, **options):
        path = options['path'] or os.path.join(
            settings.BASE_DIR, '..', 'data', 'ingredients.json'
        )
        path = os.path.abspath(path)
        count = 0
        with open(path, encoding='utf-8') as jsonfile:
            data = json.load(jsonfile)
            for item in data:
                name = item.get('name', '').strip()
                unit = item.get('measurement_unit', '').strip()
                if not name or not unit:
                    continue
                obj, created = Ingredient.objects.get_or_create(
                    name=name,
                    measurement_unit=unit,
                )
                if created:
                    count += 1
        self.stdout.write(
            self.style.SUCCESS(f'Импортировано ингредиентов: {count}')
        )
