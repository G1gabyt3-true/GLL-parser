# Character Scraper

Парсер для сбора данных о персонажах с сайта [gll-fun.com](https://gll-fun.com/ru/tierlist/identities). Извлекает информацию о навыках по выбранной категории (например, "Огонь", "Гнев") и сортирует по максимальному урону. Результаты отображаются в GUI и могут быть экспортированы в CSV.

## Возможности
- Выбор категории фильтра (грехи, типы урона, статусы).
- Парсинг персонажей и их навыков с сайта.
- Отображение результатов в таблице.
- Экспорт данных в CSV.
- Логирование в файл `scraper.log`.

## Установка
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/<your-username>/character-scraper.git
   cd character-scraper
   ```
2. Создайте и активируйте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Запустите приложение:
   ```bash
   python scraper_gui.py
   ```

## Требования
- Python 3.8+
- Зависимости из `requirements.txt`

## Использование
1. Выберите категорию в выпадающем меню (например, "Огонь").
2. Нажмите "Запустить парсинг".
3. Дождитесь завершения (прогресс отображается в прогресс-баре).
4. Просмотрите результаты в таблице.
5. Нажмите "Экспортировать в CSV" для сохранения данных.

## Сборка в .exe
1. Установите PyInstaller:
   ```bash
   pip install pyinstaller
   ```
2. Выполните сборку:
   ```bash
   pyinstaller --onefile --windowed --name CharacterScraper scraper_gui.py
   ```
3. Найдите `CharacterScraper.exe` в папке `dist/`.

## Логи
- Подробные логи сохраняются в `scraper.log`.
- В GUI отображаются только ключевые сообщения и ошибки.

## Лицензия
MIT License