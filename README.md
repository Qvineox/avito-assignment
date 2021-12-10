# Тестовое задание 
Тестовое задание на позицию стажера-бэкендера. Микросервис для работы с балансом пользователей.

## Описание выполненной задачи
Задча выполнена в полной мере. Для создания микросервиса был использован фреймворк Python Django REST Framework. Для управления данными используется СУБД PostgreSQL и библотека Psycopg2. Были реализованы все основные функции, а также дополнительные. Также добавлены некоторые особенности, которые мне показали уместными (например, несколько счетов у пользователя). Реализация на Django имеет множество встроенных инструментов - в том числе панель администрирования, шаблонизации запросов, маршрутизацию запросов, авторизации и т.д. Тестирование проведено с помощью базовой библиотеки тестирования Django REST Framework. 

Все запросы являются POST для сохранения конфиденциальности важных пользовательских данных.

Для реализации всех необходимых возможностей системы используеются следующие [модели](api/models.py): 
- Транзакции (transaction) - для описания каждого проведенного перевода средств;
- Пользовательский счет (wallet) - для хранения информации о счете пользователя, в качестве внешнего ключа использует пользователя системы (auth_user);
- Пользователь (auth_user) - базовая модель для хранения пользователей приложения Django. Используется для описания каждого пользователя (в том числе администрации) системы.

Все реализованные методы и алгоритмы размещены в django-приложении [api](api). Бизнес-логика и работа с данными вынесена в [api/services.py](api/services.py). Применяемые сериализаторы находятся в [api/serializers.py](api/serializers.py).

## Шаги для размещения на локальной машине
1. Клонирование репозитория и развертывание контейнера с приложением
```
git clone https://github.com/Qvineox/avito-assignment
cd ./avito-assignment
docker-compose build
docker-compose run web python manage.py migrate
docker-compose up
```
2. Теперь необходимо инициализировать приложение и создать административный аккаунт с базовым счетом. В целях демонстрации отправляем GET-запрос в Postman:
```
http://127.0.0.1:8000/api/init
```
3. Получение логина и пароля суперпользователя. На этом моменте все необходимые предустановки выполнены.

Затем можно перейти по http://127.0.0.1:8000/admin/ для авторизации и получения доступа к административной панели.
В данной панели можно отслеживать все изменения во врея демонстрации работы системы. 

После получения доступа к панели можно зарегистрировать несколько пользователей с помощью запроса:
```
http://127.0.0.1:8000/api/registration 
```
*в теле запроса username, password, last_name, first_name*

Получив токен пользователя и используя его для авторизации запросов, можно выполнять некоторые запросы в Postman. Однако, для внесения и снятия средств требуется административный аккаунт - нужно получить его токен и вызвать следующие запросы.
```
http://127.0.0.1:8000/api/acquire
```
*в теле запроса recipient_id, total_amount, wallet_id*
```
http://127.0.0.1:8000/api/withdraw
```
*в теле запроса recipient_id, total_amount, wallet_id*

С остальными запросами можно ознакомиться в закрепленном файле Postman. Они довольно простые и понять что к чему можно по описанию ключей в теле запроса.

## Выполненные основные и дополнительные задачи
- [x] Учетные записи
  - [x] Регистрация пользователей
  - [x] Авторизация запросов по токенам
- [ ] Денежные средства на балансе пользователей
  - [x]  *Реализация нескольких счетов (кошельков) у каждого пользователя*
  - [x]  Просмотр общего баланса
  - [x]  *Просмотр баланса по каждому счету*
  - [x]  *Просмотр баланса в валюте*
  - [ ]  *Перевод средств между своими счетами*
- [x] Транзакции между пользователями
  - [x] Перевод средств между 2 пользователями
  - [x] *Снятие средств с определенного счета пользователя*
  - [x] Алгоритмы валидации и подтверждения транзакций
  - [x] *Типы транзакций и добавление описания*
  - [x] Внесение всех транзакций в базу данных
- [x] Внесение и с вывод средств из платженой системы
  - [x] Внесение средств на счет через учетную запись администратора
  - [x] Вывод средств со счета через учетную запись администратора
  - [x] *Вывод средств с определенного счета*
- [x] *Просмотр списка всех транзакций определенного пользователя*
  - [x] *Сортировка по дате или сумме*
  - [x] *Выбор направление сортировки*
  - [x] *Реализация вывода определенного количества записей*
  - [ ] *Реализация полноценного механизма пагинации*
- [x] Тестирование
- [ ] Размещение

Нереализованные задачи в качестве интересных идей на будущее*

## Взаимодействие с API и примеры запросов
Разработка API велась с помошью Postman, *файл-коллекция запросов экспортирована в корневой каталог репозитория*. Для демонстрации можно использовать подготовленные мной запросы. Для этого нужно применить POST-запросы для регистрации и получения токена, а затем установить его в качестве метода авторизации в качестве переменных коллекции Postman.

```
http://127.0.0.1:8000/registration

http://127.0.0.1:8000/api-token-auth
```
Для применения системных методов (внесение и вывод средств из платежной системы) нужно получить токен администратора. По умолчанию после инициализации создается 1 аккаунт суперпользователя:
```
{
    "username": "avito",
    "password": "avito"
}
```
После установки ключей можно применить все виды предложенных запросов, например:

```
http://127.0.0.1:8000/api/balance?currency=USD

{
    "total_balance": 200.0,
    "exchange_total": 2.7149,
    "exchange_ratio": 73.6685,
    "exchange_currency": "USD"
}
```

## Тестирование
Тестирование проводилось с помощью UNIT-тестирования базовой библиотеки *rest_framework.test*. Тестирование проводилосб по каждому запросу с учетом особенностей каждого метода. Тесты выполнены успешно, все результаты положительны.

## Контейнер с приложением

В контейнере 2 докер-образа - для django приложения (web) и для СУБД (db). Проброшен по умолчанию порт 8000. 







