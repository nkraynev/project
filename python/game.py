"""Snake game logic without pygame, so it can be tested with pytest.

A port of game.js. Directions are (dx, dy) tuples, cells are (x, y) tuples.
"""
import random as _random
from pathlib import Path

COLS = 20
ROWS = 20
BASE_SPEED = 150  # ms per step at the start
SPEED_STEP = 8    # ms faster every 10 points
MIN_SPEED = 60
SMOOTH = 0.8      # share of a step spent sliding between cells (less = snappier)
MAX_QUEUE = 3
BEST_FILE = Path(__file__).with_name("best.txt")

UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Russian layout is supported too: ц ы ф в = w s a d
KEY_DIRS = {
    "w": UP, "ц": UP,
    "s": DOWN, "ы": DOWN,
    "a": LEFT, "ф": LEFT,
    "d": RIGHT, "в": RIGHT,
}


def key_to_direction(key):
    return KEY_DIRS.get(str(key).lower())


def current_speed(score):
    return max(MIN_SPEED, BASE_SPEED - score // 10 * SPEED_STEP)


def should_turn_now(acc, score):
    """The snake has finished sliding into its cell, so a turn can be applied right now.

    acc = ms elapsed since the last step.
    """
    return acc >= current_speed(score) * SMOOTH


def load_best(path=BEST_FILE):
    try:
        return int(Path(path).read_text().strip())
    except (OSError, ValueError):
        return 0


def save_best(best, path=BEST_FILE):
    try:
        Path(path).write_text(str(best))
    except OSError:
        pass


def place_food(snake, rng=_random.random):
    """rng() returns a float in [0, 1), like random.random. None if the field is full."""
    if len(snake) >= COLS * ROWS:
        return None
    while True:
        food = (int(rng() * COLS), int(rng() * ROWS))
        if food not in snake:
            return food


class State:
    def __init__(self, rng=None, best_path=None):
        self.rng = rng or _random.random
        self.best_path = best_path  # None: the record is not stored
        self.snake = [(10, 10), (9, 10), (8, 10)]
        self.dir = RIGHT
        self.input_queue = []
        self.food = place_food(self.snake, self.rng)
        self.score = 0
        self.best = load_best(best_path) if best_path else 0
        self.alive = True
        self.won = False


def create_state(rng=None, best_path=None):
    return State(rng, best_path)


def queue_direction(state, d):
    """Queue a turn so quick presses are not lost. Returns True if it was queued."""
    last = state.input_queue[-1] if state.input_queue else state.dir
    same = d == last
    reverse = d == (-last[0], -last[1])  # no 180° turns
    if same or reverse or len(state.input_queue) >= MAX_QUEUE:
        return False
    state.input_queue.append(d)
    return True


def step(state):
    """One game tick. Returns 'moved' | 'ate' | 'won' | 'dead'.

    'dead' is also returned if the game is already over; 'won' when the snake fills the field.
    """
    if not state.alive:
        return "dead"
    if state.input_queue:
        state.dir = state.input_queue.pop(0)
    head = (state.snake[0][0] + state.dir[0], state.snake[0][1] + state.dir[1])

    hit_wall = not (0 <= head[0] < COLS and 0 <= head[1] < ROWS)
    # the tail leaves its cell this turn unless the snake eats, so only then it is not an obstacle
    will_eat = state.food is not None and head == state.food
    body = state.snake if will_eat else state.snake[:-1]
    if hit_wall or head in body:
        state.alive = False
        return "dead"

    state.snake.insert(0, head)
    if will_eat:
        state.score += 1
        if state.score > state.best:
            state.best = state.score
            if state.best_path:
                save_best(state.best, state.best_path)
        state.food = place_food(state.snake, state.rng)
        if state.food is None:  # no free cell left: the player has won
            state.alive = False
            state.won = True
            return "won"
        return "ate"
    state.snake.pop()
    return "moved"
