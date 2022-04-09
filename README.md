# Дипломная работа Алексея Кощеева. Яндекс.Практикум Бэкенд-разработка
![My Workflow status](https://github.com/firefoxkid/foodgram-project-react/actions/workflows/main.yml/badge.svg)

### Об авторе

Алексей Кощеев 
glazov70000@yandex.ru
Телеграмм: https://t.me/Firefoxkid
  
### Тестирование проекта
Дэбаг отключен. Адрес проекта:
http://51.250.15.194

Администрирование:
http://51.250.15.194/admin

123root
foxak47789321

### О проекте

Проект "Foodgram" предоставляет собой сервис, в котором пользователи создают и публикуют свои рецепты. 
Для создания рецепта необходимо:
  - состав ингридиентов
  - описание
  - фото блюда
  - время приготовления
  - тэги
Пользователь может подписывать на других пользователей, и следить за их обновлениями.
Также рецепты можно добавлять в избранное, и список покупок из которого можно сформировать общий список необходимых ингридиентов.

### Установка для тестирования api проекта
Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone https://github.com/firefoxkid/foodgram-project-react.git
```

```bash
cd "директория проекта"
```

Cоздать и активировать виртуальное окружение:

```bash
python3 -m venv env
```

```bash
source venv/bin/activate
```

```bash
python3 -m pip install --upgrade pip
```

Установить зависимости из файла requirements.txt:

```bash
pip install -r foodgram/requirements.txt
```

Выполнить миграции:

```bash
python3 manage.py migrate
```

Запустить проект:

```bash
python3 manage.py runserver
```

### Документация 
Проект создан в соответсвии техзаданием и на основе API-документации
