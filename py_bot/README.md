# ЛР3 - Telegram-бот «Диспетчер Цеха»

Бот не играет в игру, а читает её выгрузки: `factory_layout.txt`, `factory_save.json`, `scores.csv`.

## Запуск

1. Создать бота у [@BotFather](https://t.me/BotFather), получить токен.
2. Скопировать `.env.example` в `.env` и прописать `BOT_TOKEN`, при желании `ADMIN_ID`.
3. Установить зависимости и запустить:

```powershell
python -m pip install -r py_bot/requirements.txt
python -m py_bot.bot
```

Файл `.env` в git не попадает.

## Команды

- `/start` - меню
- `/top` - рейтинг по эффективности конвейера: `детали / ходы` (чем больше, тем лучше)
- `/stats` - статистика игрока по имени из сессии
- `/upload` - приём layout-файла с проверкой символов
- `/watch` - подписка на уведомления
- `/broadcast` - рассылка подписчикам (только `ADMIN_ID`)

Сессии лежат в `sessions/<user_id>.json`. Лог: `bot_flight.log`.

## Пример сессии

```json
{
  "user_id": 123,
  "state": "MENU",
  "player_name": "Mark",
  "watch": true,
  "uploads": 1
}
```

## Тесты без сети

```powershell
python -m unittest discover -s tests_bot -v
```

Проверяются `analytics` и `session`, бот импортируется без запуска polling.
