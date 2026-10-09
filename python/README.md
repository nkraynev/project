# Змейка на Python (pygame)

Та же игра, что и `snake.html`, но на Python 3 и pygame.

Управление: **W / A / S / D** (или **Ц / Ф / Ы / В** в русской раскладке). После проигрыша или победы: **Пробел** или **Enter** — играть снова, **1–6** — выбрать скин. Рекорд хранится в файле `best.txt` рядом с игрой.

## Структура

- `game.py` — логика игры без pygame (движение, повороты, еда, столкновения, победа, скорость, рекорд)
- `main.py` — отрисовка и ввод с клавиатуры на pygame
- `test_game.py` — тесты логики на pytest (сценарии перенесены из `game.test.js`)
- `requirements.txt` — зависимости

## Установка

Нужен Python 3.9 или новее. Из папки `python/`:

```
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск игры

```
python main.py
```

## Тесты

```
pytest
```
