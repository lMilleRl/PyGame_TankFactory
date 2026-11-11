# ЛР4. Ядро на JavaScript

Та же логика сетки, конвейеров и сборки, что в Python, без отрисовки. Запуск в Node.

## Запуск

```powershell
cd tank_factory_js
node selftest.js
```

В `package.json` указано `"type": "module"`.

## Структура

```text
tank_factory_js/
├── package.json
├── selftest.js
├── README.md
└── js/
    ├── FactoryGrid.js
    ├── Drone.js
    ├── Conveyor.js
    ├── PartStack.js
    └── layout.js
```

Уровень читается из `../factory_layout.txt` (общий с игрой).

## Соответствие Python -> JS

| Python | JavaScript |
|--------|------------|
| `Factory` | `FactoryGrid` |
| `Drone` | `Drone` |
| `Conveyor` | `Conveyor` |
| `assembly_stack` + проверка порядка | `PartStack` (`.push()`, `.join()`) |
| `tank_factory/layout.py` | `js/layout.js` |

Сборка считается верной, если `items.join(",") === "chassis,turret,cannon"`.

Каждый успешный ход увеличивает `turnCount` и сдвигает детали на конвейерах.

Последний запуск самопроверки: 28 OK, 0 FAIL.
