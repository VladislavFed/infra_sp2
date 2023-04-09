# Проект api_yamdb

Проект курса "Python-разработчик плюс"

### Технологии

Django, DRF

### Авторы

Никита Артимович, Николай Морозов, Владислав Федотов

### Документация к API

`/redoc/` - Документация к API проекта

### Пример запроса к API

`GET /api/v1/titles/` - получение списка всех произведений.

Пример ответа:
HTTP Response 200
```json
{
  "count": 0,
  "next": "string",
  "previous": "string",
  "results": [
    {
      "id": 0,
      "name": "string",
      "year": 0,
      "rating": 0,
      "description": "string",
      "genre": [
        {
          "name": "string",
          "slug": "string"
        }
      ],
      "category": {
        "name": "string",
        "slug": "string"
      }
    }
  ]
}
```

### Как запустить проект:

Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone git@github.com:nartim88/api_yamdb.git
```

```bash
cd api_yamdb
```

Cоздать и активировать виртуальное окружение:

```bash
python3 -m venv env
```

* Если у вас Linux/macOS

    ```bash
    source env/bin/activate
    ```

* Если у вас windows

    ```bash
    source env/scripts/activate
    ```

```bash
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```bash
pip install -r requirements.txt
```

Выполнить миграции:

```bash
python3 manage.py migrate
```

Запустить проект:

```bash
python3 manage.py runserver
```

### Заполнение БД из CSV файлов

Команда вызывается как 
        ```
        python manage.py populatedb -s .. -t ...
        ```
и требует наличия двух флагов:
    
После флага -t[--target] указываются имена моделей, которые нужно заполнить данными.
Названия не чувствительны к регистру: -t User = -t user

После флага -s[--source] указываются имена файлов, из которых требуется извлечь данные.
Указывается только *название* файла, которое далее ищется в директории data в статике проекта.

В случае, если требуется заполнить все таблицы БД, следует использовать флаг --full.
    
В команду могут передаваться несколько моделей и файлов через пробел, однако их число должно совпадать и их 
последовательность должна быть соответствующей:
    ```
    python3 manage.py populatedb -t Category Genre -s category.csv genre.csv
    ```

Внимание:
    Команда выполняет парсинг и заполнение в порядке, указанном пользователем. Это значит, что
    перед заполнением таблицы связи ManyToMany надо заполнить связанные с ней таблицы, иначе
    будет получена ошибка нарушения constraint.

Неправильно:
        ```
        python3 manage.py -t TitleGenre Title Genre -s ...
        ```
    Правильно:
        ```
        python3 manage.py -t Title Genre TitleGenre -s ...
        ```


### Шаблон наполнения env-файла:

   ```python
   DB_ENGINE= #указываем с чем работаем 

   DB_NAME= #имя БД 

   POSTGRES_USER= #логин для подключения 

   POSTGRES_PASSWORD= #пароль для подключения 

   DB_HOST= название #контейнера 

   DB_PORT= #порт для подключения к БД
   ``` 

