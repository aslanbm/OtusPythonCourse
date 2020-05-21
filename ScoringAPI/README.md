# Scoring API 

 
1) Для запуска http сервера используем `python api.py`
Есть возможность указать порт и путь до логфайла при запуске.

`python api.py --log [log_file] --p [port]`

Для отправки запросов на сервер пользуемся утилитой curl. Формат словаря с аргументами смотреть в `homework.pdf`.
`curl -X POST -H "Content-Type: application/json" -d {dict} http://127.0.0.1:{port}/method`

2) Есть возможность использовать 2 функции: `client_interests`, `online_score`. Их реализация в скрипте `scoring.py`

3) Тесты для проверки нашего API реализованы в скрипте `test.py`. Запуск тестов: `python -m unittest test.py`

