// Snake game logic without DOM/canvas, so it can be tested in Node.
// In the browser it is exposed as the global `SnakeGame`.
(function (root) {
  const COLS = 20;
  const ROWS = 20;
  const BASE_SPEED = 150;  // ms per step at the start
  const SPEED_STEP = 8;    // ms faster every 10 points
  const MIN_SPEED = 60;
  const SMOOTH = 0.8;      // share of a step spent sliding between cells (less = snappier)
  const BEST_KEY = 'snakeBest';
  const MAX_QUEUE = 3;

  // Russian layout is supported too: ц ы ф в = w s a d
  const KEY_DIRS = {
    w: { x: 0, y: -1 }, 'ц': { x: 0, y: -1 },
    s: { x: 0, y: 1 },  'ы': { x: 0, y: 1 },
    a: { x: -1, y: 0 }, 'ф': { x: -1, y: 0 },
    d: { x: 1, y: 0 },  'в': { x: 1, y: 0 },
  };

  function keyToDirection(key) {
    const d = KEY_DIRS[String(key).toLowerCase()];
    return d ? { ...d } : null;
  }

  function currentSpeed(score) {
    return Math.max(MIN_SPEED, BASE_SPEED - Math.floor(score / 10) * SPEED_STEP);
  }

  // The snake has finished sliding into its cell, so a fresh turn can be applied right now
  // instead of waiting for the next tick. acc = ms elapsed since the last step.
  function shouldTurnNow(acc, score) {
    return acc >= currentSpeed(score) * SMOOTH;
  }

  function loadBest(storage) {
    try { return parseInt(storage.getItem(BEST_KEY), 10) || 0; } catch (e) { return 0; }
  }

  function saveBest(storage, best) {
    try { storage.setItem(BEST_KEY, best); } catch (e) {}
  }

  // random() returns a number in [0, 1), like Math.random
  function placeFood(snake, random = Math.random) {
    if (snake.length >= COLS * ROWS) return null; // no free cell left
    let food;
    do {
      food = { x: Math.floor(random() * COLS), y: Math.floor(random() * ROWS) };
    } while (snake.some(s => s.x === food.x && s.y === food.y));
    return food;
  }

  // options: { random, storage }
  function createState(options = {}) {
    const random = options.random || Math.random;
    const storage = options.storage || null;
    const snake = [{ x: 10, y: 10 }, { x: 9, y: 10 }, { x: 8, y: 10 }];
    return {
      snake,
      dir: { x: 1, y: 0 },
      inputQueue: [],
      food: placeFood(snake, random),
      score: 0,
      best: storage ? loadBest(storage) : 0,
      alive: true,
      random,
      storage,
    };
  }

  // Queue a turn so quick presses are not lost. Returns true if it was queued.
  function queueDirection(state, d) {
    // check against the last queued direction, not the current one
    const last = state.inputQueue.length ? state.inputQueue[state.inputQueue.length - 1] : state.dir;
    const same = d.x === last.x && d.y === last.y;
    const reverse = d.x === -last.x && d.y === -last.y; // no 180° turns
    if (same || reverse || state.inputQueue.length >= MAX_QUEUE) return false;
    state.inputQueue.push(d);
    return true;
  }

  // One game tick. Returns 'moved' | 'ate' | 'dead' (also 'dead' if the game is already over).
  function step(state) {
    if (!state.alive) return 'dead';
    if (state.inputQueue.length) state.dir = state.inputQueue.shift();
    const head = { x: state.snake[0].x + state.dir.x, y: state.snake[0].y + state.dir.y };

    const hitWall = head.x < 0 || head.y < 0 || head.x >= COLS || head.y >= ROWS;
    const hitSelf = state.snake.some(s => s.x === head.x && s.y === head.y);
    if (hitWall || hitSelf) {
      state.alive = false;
      return 'dead';
    }

    state.snake.unshift(head);
    if (state.food && head.x === state.food.x && head.y === state.food.y) {
      state.score++;
      if (state.score > state.best) {
        state.best = state.score;
        if (state.storage) saveBest(state.storage, state.best);
      }
      state.food = placeFood(state.snake, state.random);
      return 'ate';
    }
    state.snake.pop();
    return 'moved';
  }

  const api = {
    COLS, ROWS, BASE_SPEED, SPEED_STEP, MIN_SPEED, SMOOTH, BEST_KEY,
    keyToDirection, currentSpeed, shouldTurnNow, loadBest, saveBest,
    placeFood, createState, queueDirection, step,
  };

  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.SnakeGame = api;
})(typeof window !== 'undefined' ? window : globalThis);
