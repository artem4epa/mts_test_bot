# Бот техподдержки
## Функционал.
Этот бот позволяет отправлять заявку в сервис техподдержки по API. 
## Технологии  
1. Python 3.10
2. Aiogram 3.0
3. Requests

## Запуск в режиме разработки
В первую очередь создаем телеграм бота и при помощи @BotFather, получаем токен.
1. Клонирование репозитория.  
```
git clone git@github.com:artem4epa/mts_test_bot.git # Клонируем репозиторий
```
2. Установка виртуального окружения
```
pythom -m venv venv
```
3. Установка зависимостей
```
pip install -r requirements.txt
```
4. Кладем токен бота в файл ```.env``` в переменную ```TELEGRAM_TOKEN```
5. Проверяем доступность, по необходимости меняем адрес в переменной ```SERVER_API``` api сервиса для отрпавки заявок в файле ```.env``` 
3. Запуск 
```
python mts_test_bot.py
```

## Автор
artem4epa  
Бот: username = @mts_test_che_bot