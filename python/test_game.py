import pytest

import game as G
from game import UP, DOWN, LEFT, RIGHT


def make_state(**overrides):
    """Snake at (10,10),(9,10),(8,10) heading right, food placed explicitly."""
    s = G.create_state(rng=lambda: 0)
    s.food = (0, 0)
    for k, v in overrides.items():
        setattr(s, k, v)
    return s


def full_field_snake():
    """Zigzag snake covering the whole field except (0, ROWS-1); the head is next to it."""
    path = []
    for y in range(G.ROWS):
        xs = list(range(G.COLS))
        if y % 2 == 1:
            xs.reverse()
        path += [(x, y) for x in xs]
    path.pop()
    path.reverse()
    return path


def test_initial_state():
    s = G.create_state(rng=lambda: 0.1)
    assert s.snake == [(10, 10), (9, 10), (8, 10)]
    assert s.dir == RIGHT
    assert s.score == 0
    assert s.alive is True
    assert s.input_queue == []


# --- movement ---

def test_step_moves_one_cell_length_unchanged():
    s = make_state()
    assert G.step(s) == "moved"
    assert s.snake == [(11, 10), (10, 10), (9, 10)]


def test_step_applies_queued_turn():
    s = make_state()
    G.queue_direction(s, UP)
    G.step(s)
    assert s.dir == UP
    assert s.snake[0] == (10, 9)
    assert s.input_queue == []


# --- turning ---

def test_perpendicular_turn_is_queued():
    s = make_state()
    assert G.queue_direction(s, UP) is True
    assert s.input_queue == [UP]


def test_180_turn_is_ignored():
    s = make_state()
    assert G.queue_direction(s, LEFT) is False
    assert s.input_queue == []


def test_180_turn_is_checked_against_last_queued_direction():
    s = make_state()
    G.queue_direction(s, UP)
    assert G.queue_direction(s, DOWN) is False  # reverse of queued UP
    assert G.queue_direction(s, LEFT) is True   # allowed after UP
    assert s.input_queue == [UP, LEFT]


def test_current_direction_again_is_ignored():
    s = make_state()
    assert G.queue_direction(s, RIGHT) is False
    assert s.input_queue == []


def test_input_queue_holds_at_most_3_turns():
    s = make_state()
    assert G.queue_direction(s, UP) is True
    assert G.queue_direction(s, LEFT) is True
    assert G.queue_direction(s, DOWN) is True
    assert G.queue_direction(s, RIGHT) is False
    assert len(s.input_queue) == 3


def test_quick_double_turn_does_not_run_into_itself():
    s = make_state()
    G.queue_direction(s, UP)
    G.queue_direction(s, LEFT)
    assert G.step(s) == "moved"
    assert G.step(s) == "moved"
    assert s.snake[0] == (9, 9)
    assert s.alive is True


@pytest.mark.parametrize("key,expected", [
    ("w", UP), ("S", DOWN), ("a", LEFT), ("d", RIGHT),
    ("ц", UP), ("ы", DOWN), ("ф", LEFT), ("В", RIGHT),
    ("x", None), ("ArrowUp", None), ("", None),
])
def test_key_to_direction(key, expected):
    assert G.key_to_direction(key) == expected


# --- eating and growth ---

def test_eating_grows_snake_and_adds_point():
    s = make_state(food=(11, 10))
    assert G.step(s) == "ate"
    assert len(s.snake) == 4
    assert s.snake[0] == (11, 10)
    assert s.snake[3] == (8, 10)  # tail stays in place
    assert s.score == 1


def test_after_eating_new_food_is_on_a_free_cell():
    s = make_state(food=(11, 10))
    seq = iter([0.5, 0.5, 0.25, 0.75])  # (10,10) is occupied, then (5,15) is free
    s.rng = lambda: next(seq)
    G.step(s)
    assert s.food == (5, 15)


def test_no_growth_and_no_points_without_food():
    s = make_state()
    G.step(s)
    assert len(s.snake) == 3
    assert s.score == 0


# --- collisions ---

def test_hitting_right_wall_ends_game():
    s = make_state(snake=[(G.COLS - 1, 5), (G.COLS - 2, 5), (G.COLS - 3, 5)])
    assert G.step(s) == "dead"
    assert s.alive is False


@pytest.mark.parametrize("snake,direction", [
    ([(0, 5), (1, 5), (2, 5)], LEFT),
    ([(5, 0), (5, 1), (5, 2)], UP),
    ([(5, G.ROWS - 1), (5, G.ROWS - 2), (5, G.ROWS - 3)], DOWN),
])
def test_hitting_each_wall_ends_game(snake, direction):
    s = make_state(snake=snake, dir=direction)
    assert G.step(s) == "dead"
    assert s.alive is False


def test_moving_along_wall_is_alive():
    s = make_state(snake=[(G.COLS - 2, 5), (G.COLS - 3, 5), (G.COLS - 4, 5)])
    assert G.step(s) == "moved"
    assert s.snake[0][0] == G.COLS - 1
    assert s.alive is True


def test_running_into_own_body_ends_game():
    s = make_state(snake=[(5, 5), (6, 5), (6, 6), (5, 6), (4, 6)], dir=LEFT)
    G.queue_direction(s, DOWN)  # (5,6) is the second to last cell, not the tail
    assert G.step(s) == "dead"
    assert s.alive is False


def test_head_may_enter_cell_tail_is_leaving():
    s = make_state(snake=[(5, 5), (6, 5), (6, 6), (5, 6)], dir=LEFT)
    G.queue_direction(s, DOWN)
    assert G.step(s) == "moved"
    assert s.alive is True
    assert s.snake == [(5, 6), (5, 5), (6, 5), (6, 6)]


def test_when_eating_tail_stays_and_its_cell_is_a_collision():
    # artificial case: food lies on the tail cell
    s = make_state(snake=[(5, 5), (6, 5), (6, 6), (5, 6)], dir=LEFT, food=(5, 6))
    G.queue_direction(s, DOWN)
    assert G.step(s) == "dead"
    assert s.alive is False


def test_chasing_own_tail_for_many_laps():
    s = make_state(snake=[(5, 5), (6, 5), (6, 6), (5, 6)], dir=LEFT)
    for d in [DOWN, RIGHT, UP, LEFT] * 2:
        G.queue_direction(s, d)
        assert G.step(s) == "moved"
    assert s.alive is True
    assert len(s.snake) == 4


def test_dead_snake_does_not_move():
    s = make_state()
    s.alive = False
    before = list(s.snake)
    assert G.step(s) == "dead"
    assert s.snake == before


# --- food placement ---

def test_place_food_never_on_snake():
    snake = [(0, 0), (1, 0), (2, 0)]
    # rng yields the occupied cells first, then a free one
    seq = iter([0, 0, 0.05, 0, 0.1, 0, 0.5, 0.5])
    assert G.place_food(snake, lambda: next(seq)) == (10, 10)
    assert list(seq) == []


def test_place_food_stays_inside_field():
    assert G.place_food([(0, 0)], lambda: 0.999999) == (G.COLS - 1, G.ROWS - 1)


def test_place_food_with_real_randomness_never_on_snake():
    snake = [(x, y) for x in range(G.COLS) for y in range(G.ROWS - 1)]
    for _ in range(200):
        assert G.place_food(snake)[1] == G.ROWS - 1


def test_place_food_returns_none_when_field_is_full():
    snake = [(x, y) for x in range(G.COLS) for y in range(G.ROWS)]
    assert G.place_food(snake) is None


# --- victory ---

def test_eating_last_free_cell_wins():
    snake = full_field_snake()
    s = make_state(snake=snake, dir=LEFT, food=(0, G.ROWS - 1))
    assert s.snake[0] == (1, G.ROWS - 1)
    assert G.step(s) == "won"
    assert s.won is True
    assert s.alive is False
    assert s.food is None
    assert len(s.snake) == G.COLS * G.ROWS
    assert G.step(s) == "dead"  # the game is over


def test_normal_game_is_not_won():
    s = make_state(food=(11, 10))
    assert G.step(s) == "ate"
    assert s.won is False


# --- speed ---

def test_speed_increases_every_10_points():
    assert G.current_speed(0) == G.BASE_SPEED
    assert G.current_speed(9) == G.BASE_SPEED
    assert G.current_speed(10) == G.BASE_SPEED - G.SPEED_STEP
    assert G.current_speed(19) == G.BASE_SPEED - G.SPEED_STEP
    assert G.current_speed(20) == G.BASE_SPEED - 2 * G.SPEED_STEP


def test_speed_never_below_min():
    assert G.current_speed(10000) == G.MIN_SPEED


# --- immediate turn ---

def test_should_turn_now_false_while_sliding():
    assert G.should_turn_now(0, 0) is False
    assert G.should_turn_now(G.BASE_SPEED * G.SMOOTH - 1, 0) is False


def test_should_turn_now_true_after_slide_before_next_tick():
    assert G.should_turn_now(G.BASE_SPEED * G.SMOOTH, 0) is True
    assert G.should_turn_now(G.BASE_SPEED - 1, 0) is True


def test_smooth_is_below_one():
    # acc is always below the step interval, so with SMOOTH = 1 the branch would be dead code
    assert G.SMOOTH < 1


def test_should_turn_now_follows_speed_up():
    fast = G.current_speed(10) * G.SMOOTH
    assert G.should_turn_now(fast, 10) is True
    assert G.should_turn_now(fast, 0) == (fast >= G.BASE_SPEED * G.SMOOTH)


# --- best score (stored in a file) ---

def test_best_is_loaded_from_file(tmp_path):
    f = tmp_path / "best.txt"
    f.write_text("42")
    assert G.create_state(best_path=f).best == 42


def test_best_is_zero_if_file_missing_or_broken(tmp_path):
    assert G.create_state(best_path=tmp_path / "none.txt").best == 0
    f = tmp_path / "best.txt"
    f.write_text("abc")
    assert G.create_state(best_path=f).best == 0
    assert G.create_state(best_path=tmp_path).best == 0  # a directory, not a file


def test_new_record_is_saved(tmp_path):
    f = tmp_path / "best.txt"
    f.write_text("0")
    s = G.create_state(rng=lambda: 0, best_path=f)
    s.food = (11, 10)
    G.step(s)
    assert s.best == 1
    assert f.read_text() == "1"


def test_score_below_record_does_not_overwrite_it(tmp_path):
    f = tmp_path / "best.txt"
    f.write_text("5")
    s = G.create_state(rng=lambda: 0, best_path=f)
    s.food = (11, 10)
    G.step(s)
    assert s.score == 1
    assert s.best == 5
    assert f.read_text() == "5"


def test_failing_storage_does_not_break_the_game(tmp_path):
    s = G.create_state(rng=lambda: 0, best_path=tmp_path / "no_such_dir" / "best.txt")
    s.food = (11, 10)
    G.step(s)  # must not raise
    assert s.best == 1
