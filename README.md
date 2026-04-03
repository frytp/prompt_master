# Prompt Manager

Веб-приложение для управления промптами для работы с AI-моделями.

## Описание

Prompt Manager помогает организовать и хранить готовые промпты для различных AI-моделей (ChatGPT, Claude, Gemini). Приложение позволяет:

- Создавать и редактировать промпты
- Организовывать промпты по категориям и тегам
- Фильтровать и искать промпты
- Импортировать готовые наборы промптов из JSON
- Копировать промпты в буфер обмена одним кликом

## Технологии

- Python 3.10+
- Django 5.0
- Bootstrap 5
- SQLite

## Установка и запуск

### 1. Клонировать репозиторий
```bash
git clone https://github.com/your-username/prompt-manager.git
cd prompt-manager
```

### 2. Создать виртуальное окружение
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Установить зависимости
```bash
pip install -r requirements.txt
```

### 4. Применить миграции
```bash
python manage.py migrate
```

### 5. Загрузить предустановленные данные (опционально)
```bash
python manage.py loaddata prompts/fixtures/initial_data.json
```

### 6. Создать суперпользователя
```bash
python manage.py createsuperuser
```

### 7. Запустить сервер
```bash
python manage.py runserver
```

Приложение будет доступно по адресу: http://127.0.0.1:8000/

## Импорт промптов

Для импорта промптов из JSON файла:

1. Перейдите в раздел "Импорт" в навигационном меню
2. Загрузите JSON файл с промптами
3. Пример структуры файла находится в `sample_prompts.json`

## Структура проекта
```
prompt_manager/
├── config/              # Настройки Django
├── prompts/             # Основное приложение
│   ├── fixtures/        # Предустановленные данные
│   ├── templatetags/    # Кастомные template tags
│   ├── models.py        # Модели данных
│   ├── views.py         # Представления
│   ├── forms.py         # Формы
│   └── urls.py          # URL маршруты
├── templates/           # HTML шаблоны
├── static/              # Статические файлы
└── manage.py
```

## Автор

Илья Гомжин

## Лицензия

MIPT License (нет)))))