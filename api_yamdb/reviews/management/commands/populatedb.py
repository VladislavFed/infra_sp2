import csv
import os
from pathlib import Path
from typing import List

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Model
from reviews.models import (Category, Comment, Genre, Review, Title,
                            TitleGenre, User)

CSV_DATA_PATH = os.path.join(settings.STATICFILES_DIRS[0], 'data')

MODELS = {
    'category': Category,
    'genre': Genre,
    'title': Title,
    'titlegenre': TitleGenre,
    'user': User,
    'review': Review,
    'comment': Comment
}

FOREIGN_KEYS = {
    'category': Category,
    'title': Title,
    'author': User,
}

INSERTING_ORDER = {
    'category': 'category.csv',
    'genre': 'genre.csv',
    'title': 'titles.csv',
    'titlegenre': 'genre_title.csv',
    'user': 'users.csv',
    'review': 'review.csv',
    'comment': 'comments.csv'
}


class Command(BaseCommand):
    """Management command для заполнения БД данными из указанных .csv файлов.

    Команда вызывается как
        python manage.py populatedb -s .. -t ...
    и требует наличия двух флагов:

    После флага -t[--target] указываются имена моделей,
    которые нужно заполнить данными.
    Названия не чувствительны к регистру: -t User = -t user

    После флага -s[--source] указываются имена файлов, из которых
    требуется извлечь данные.
    Указывается только *название* файла, которое далее
    ищется в директории data в статике проекта.

    В случае, если требуется заполнить все таблицы БД, следует
    использовать флаг --full.

    В команду могут передаваться несколько моделей и файлов через пробел,
    однако
    - их число должно совпадать
    - их последовательность должна быть соответствующей:

    python3 manage.py populatedb -t Category Genre -s category.csv genre.csv

    Внимание:
    Команда выполняет парсинг и заполнение в порядке, указанном пользователем.
    Это значит, что перед заполнением таблицы связи ManyToMany
    надо заполнить связанные с ней таблицы, иначе
    будет получена ошибка нарушения constraint.

    Неправильно:
        python3 manage.py -t TitleGenre Title Genre -s ...
    Правильно:
        python3 manage.py -t Title Genre TitleGenre -s ...

    """
    help = 'Populates database with data from .csv files'

    def add_arguments(self, parser):
        parser.add_argument(
            '-t',
            '--target',
            nargs='+',
            type=str,
            help='Названия моделей, которые следует заполнить'
        )
        parser.add_argument(
            '-s',
            '--source',
            nargs='+',
            type=str,
            help='Названия csv файлов для выгрузки данных'
        )
        parser.add_argument(
            '--full',
            action='store_true'
        )

    def handle(self, *args, **options):
        if options['full']:
            target_model_names = INSERTING_ORDER.keys()
            source_file_paths = INSERTING_ORDER.values()
        else:
            target_model_names = options['target']
            source_file_paths = options['source']

        try:
            source_files = self._validate_source_kwarg(source_file_paths)
            target_models = self._validate_target_kwarg(target_model_names)
        except CommandError as e:
            raise e

        if len(source_files) != len(target_models):
            raise CommandError(
                '''
                Number of csv files and corresponding
                models should be the same
                '''
            )

        csv_to_models = dict(zip(target_models, source_files))

        print('Models and source files are parsed. Started extracting')
        for model, source in csv_to_models.items():
            with open(source, 'r', encoding='utf-8') as csv_file:
                try:
                    reader = csv.DictReader(csv_file)
                    objects = []

                    for row in reader:
                        row = self._update_foreign_values(row)
                        objects.append(row)

                    model.objects.bulk_create(
                        model(**data)
                        for data in objects
                    )
                except Exception as e:
                    raise CommandError(f'Error while populating {model}: {e}')

        self.stdout.write(self.style.SUCCESS('DB successfully populated'))

    def _update_foreign_values(self, record):
        """Заменяет внешний ключ в записи на сам объект,
        на который он ссылается.

        Заменяет значения внешних ключей в словаре на сами инстансы модели.
        "id" = 1 -> "id" = model.objects.get(pk=1)
        Для дальнейшней передачи в create() или bulk_create().

        Args:
            record: Словарь, представляющий собой запись из таблицы
        Returns:
            Словарь с подставленными вместо внешних ключей объектами
        Raises:
            CommandError: Объект с таким внешним ключем не был найден.
        """
        for field, value in record.items():
            if field in FOREIGN_KEYS:
                foreign_key_model = FOREIGN_KEYS[field]

                record[field] = foreign_key_model.objects.get(
                    pk=value
                )
                if record[field] is None:
                    raise CommandError(
                        f'''Foreign key constraint мiolation:
                        no record ащк pk={value}
                        '''
                    )
        return record

    def _validate_source_kwarg(self, sources: List[str]) -> List[Path]:
        """Проверяет валидность введенных путей к csv-файлам
        и возвращает абсолютный путь к ним.

        Поиск осуществляется в директории data в статике.

        Args:
            sources: список *имен* .csv файлов.
        Returns:
            Список полных путей переданнх .csv файлов.
        Raises:
            CommandError: Список имен пуст.
            CommandError: Файл с таким именем не найден.
        """
        if not sources:
            raise CommandError("Option `--targets=...` must be specified.")

        source_files = []

        for source in sources:
            source_file = Path(os.path.join(CSV_DATA_PATH, source))
            if not source_file.is_file():
                raise CommandError(f'Cannot parse file {source_file}')
            source_files.append(source_file)

        return source_files

    def _validate_target_kwarg(self, targets: List[str]) -> List[Model]:
        """Проверяет валидность названий моделей
        для заполнения и возвращает их классы.

        Проверяет, есть ли возможность заполнить значениями таблицу модели.

        Args:
            targets: список названий модели. Нечувствительны к регистру.
        Returns:
            Список классов, соответствующий переданным названиям.
        Raises:
            CommandError: Список названий пуст.
            CommandError: Модель с таким именем не найдена.
            CommandError: Таблица модели уже заплнена данными.
        """
        if not targets:
            raise CommandError("Option `--target=...` must be specified.")

        target_models = []

        for target in targets:
            if target.lower() not in MODELS:
                raise CommandError(f'Cannot find {target} model')
            model = MODELS[target.lower()]
            if model.objects.exists():
                raise CommandError(f'Model {target} is already populated.')
            target_models.append(model)

        return target_models
