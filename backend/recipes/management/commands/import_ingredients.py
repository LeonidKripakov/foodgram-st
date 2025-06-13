import csv
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Импорт ингредиентов из CSV-файла в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--path',
            type=str,
            help='Путь к CSV-файлу с ингредиентами'
        )

    def handle(self, *args, **options):
        path = options['path'] or os.path.join(
            settings.BASE_DIR, '..', 'data', 'ingredients.csv'
        )
        path = os.path.abspath(path)
        count = 0
        with open(path, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                obj, created = Ingredient.objects.get_or_create(
                    name=row['name'].strip(),
                    measurement_unit=row['measurement_unit'].strip(),
                )
                if created:
                    count += 1
        self.stdout.write(
            self.style.SUCCESS(f'Импортировано ингредиентов: {count}')
        )
