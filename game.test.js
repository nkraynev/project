const test = require('node:test');
const assert = require('node:assert/strict');
const G = require('./game.js');

// Fake localStorage
function memoryStorage(initial = {}) {
  const data = { ...initial };
  return {
    data,
    getItem: k => (k in data ? data[k] : null),
    setItem: (k, v) => { data[k] = String(v); },
  };
}

// State with the snake at (10,10),(9,10),(8,10) heading right and food placed explicitly
function makeState(overrides = {}) {
  const state = G.createState({ random: () => 0 });
  state.food = { x: 0, y: 0 };
  return Object.assign(state, overrides);
}

const UP = { x: 0, y: -1 };
const DOWN = { x: 0, y: 1 };
const LEFT = { x: -1, y: 0 };
const RIGHT = { x: 1, y: 0 };

test('initial state', () => {
  const s = G.createState({ random: () => 0.1 });
  assert.deepEqual(s.snake, [{ x: 10, y: 10 }, { x: 9, y: 10 }, { x: 8, y: 10 }]);
  assert.deepEqual(s.dir, RIGHT);
  assert.equal(s.score, 0);
  assert.equal(s.alive, true);
  assert.deepEqual(s.inputQueue, []);
});

// --- movement ---

test('step moves the snake one cell in its direction, length unchanged', () => {
  const s = makeState();
  assert.equal(G.step(s), 'moved');
  assert.deepEqual(s.snake, [{ x: 11, y: 10 }, { x: 10, y: 10 }, { x: 9, y: 10 }]);
});

test('step applies a queued turn', () => {
  const s = makeState();
  G.queueDirection(s, UP);
  G.step(s);
  assert.deepEqual(s.dir, UP);
  assert.deepEqual(s.snake[0], { x: 10, y: 9 });
  assert.deepEqual(s.inputQueue, []);
});

// --- turning ---

test('turn to a perpendicular direction is queued', () => {
  const s = makeState();
  assert.equal(G.queueDirection(s, UP), true);
  assert.deepEqual(s.inputQueue, [UP]);
});

test('180° turn is ignored', () => {
  const s = makeState();
  assert.equal(G.queueDirection(s, LEFT), false);
  assert.deepEqual(s.inputQueue, []);
});

test('180° turn is checked against the last queued direction, not the current one', () => {
  const s = makeState();
  G.queueDirection(s, UP);
  assert.equal(G.queueDirection(s, DOWN), false); // reverse of queued UP
  assert.equal(G.queueDirection(s, LEFT), true);  // allowed after UP
  assert.deepEqual(s.inputQueue, [UP, LEFT]);
});

test('pressing the current direction again is ignored', () => {
  const s = makeState();
  assert.equal(G.queueDirection(s, RIGHT), false);
  assert.deepEqual(s.inputQueue, []);
});

test('input queue holds at most 3 turns', () => {
  const s = makeState();
  assert.equal(G.queueDirection(s, UP), true);
  assert.equal(G.queueDirection(s, LEFT), true);
  assert.equal(G.queueDirection(s, DOWN), true);
  assert.equal(G.queueDirection(s, RIGHT), false);
  assert.equal(s.inputQueue.length, 3);
});

test('quick double turn does not run the snake into itself', () => {
  const s = makeState();
  G.queueDirection(s, UP);
  G.queueDirection(s, LEFT);
  assert.equal(G.step(s), 'moved');
  assert.equal(G.step(s), 'moved');
  assert.deepEqual(s.snake[0], { x: 9, y: 9 });
  assert.equal(s.alive, true);
});

test('keyToDirection maps WASD and Russian layout, case-insensitive', () => {
  assert.deepEqual(G.keyToDirection('w'), UP);
  assert.deepEqual(G.keyToDirection('S'), DOWN);
  assert.deepEqual(G.keyToDirection('a'), LEFT);
  assert.deepEqual(G.keyToDirection('d'), RIGHT);
  assert.deepEqual(G.keyToDirection('ц'), UP);
  assert.deepEqual(G.keyToDirection('ы'), DOWN);
  assert.deepEqual(G.keyToDirection('ф'), LEFT);
  assert.deepEqual(G.keyToDirection('В'), RIGHT);
  assert.equal(G.keyToDirection('x'), null);
  assert.equal(G.keyToDirection('ArrowUp'), null);
});

// --- eating and growth ---

test('eating food grows the snake by one and adds a point', () => {
  const s = makeState({ food: { x: 11, y: 10 } });
  assert.equal(G.step(s), 'ate');
  assert.equal(s.snake.length, 4);
  assert.deepEqual(s.snake[0], { x: 11, y: 10 });
  assert.deepEqual(s.snake[3], { x: 8, y: 10 }); // tail stays in place
  assert.equal(s.score, 1);
});

test('after eating, new food appears on a free cell', () => {
  const s = makeState({ food: { x: 11, y: 10 } });
  const seq = [0.5, 0.5, 0.25, 0.75]; // (10,10) is occupied, then (5,15) is free
  let i = 0;
  s.random = () => seq[i++];
  G.step(s);
  assert.deepEqual(s.food, { x: 5, y: 15 });
});

test('no growth and no points without food', () => {
  const s = makeState();
  G.step(s);
  assert.equal(s.snake.length, 3);
  assert.equal(s.score, 0);
});

// --- collisions ---

test('hitting the right wall ends the game', () => {
  const s = makeState();
  s.snake = [{ x: G.COLS - 1, y: 5 }, { x: G.COLS - 2, y: 5 }, { x: G.COLS - 3, y: 5 }];
  assert.equal(G.step(s), 'dead');
  assert.equal(s.alive, false);
});

test('hitting each wall ends the game', () => {
  const cases = [
    { snake: [{ x: 0, y: 5 }, { x: 1, y: 5 }, { x: 2, y: 5 }], dir: LEFT },
    { snake: [{ x: 5, y: 0 }, { x: 5, y: 1 }, { x: 5, y: 2 }], dir: UP },
    { snake: [{ x: 5, y: G.ROWS - 1 }, { x: 5, y: G.ROWS - 2 }, { x: 5, y: G.ROWS - 3 }], dir: DOWN },
  ];
  for (const c of cases) {
    const s = makeState({ snake: c.snake, dir: c.dir });
    assert.equal(G.step(s), 'dead', JSON.stringify(c.dir));
    assert.equal(s.alive, false);
  }
});

test('moving along the wall (last cell) is still alive', () => {
  const s = makeState();
  s.snake = [{ x: G.COLS - 2, y: 5 }, { x: G.COLS - 3, y: 5 }, { x: G.COLS - 4, y: 5 }];
  assert.equal(G.step(s), 'moved');
  assert.equal(s.snake[0].x, G.COLS - 1);
  assert.equal(s.alive, true);
});

test('running into own body ends the game', () => {
  // A snake curled so that heading down hits its own body
  const s = makeState({
    snake: [{ x: 5, y: 5 }, { x: 6, y: 5 }, { x: 6, y: 6 }, { x: 5, y: 6 }, { x: 4, y: 6 }],
    dir: LEFT,
  });
  G.queueDirection(s, DOWN);
  assert.equal(G.step(s), 'dead');
  assert.equal(s.alive, false);
});

test('a dead snake does not move', () => {
  const s = makeState();
  s.alive = false;
  const before = JSON.stringify(s.snake);
  assert.equal(G.step(s), 'dead');
  assert.equal(JSON.stringify(s.snake), before);
});

// --- food placement ---

test('placeFood never puts food on the snake', () => {
  const snake = [{ x: 0, y: 0 }, { x: 1, y: 0 }, { x: 2, y: 0 }];
  // random yields the occupied cells first, then a free one
  const seq = [0, 0, 0.05, 0, 0.1, 0, 0.5, 0.5];
  let i = 0;
  const food = G.placeFood(snake, () => seq[i++]);
  assert.deepEqual(food, { x: 10, y: 10 });
  assert.equal(i, seq.length);
});

test('placeFood stays inside the field (random close to 1)', () => {
  const food = G.placeFood([{ x: 0, y: 0 }], () => 0.999999);
  assert.deepEqual(food, { x: G.COLS - 1, y: G.ROWS - 1 });
});

test('placeFood with real randomness never lands on the snake', () => {
  const snake = [];
  for (let x = 0; x < G.COLS; x++) for (let y = 0; y < G.ROWS - 1; y++) snake.push({ x, y });
  for (let n = 0; n < 200; n++) {
    const f = G.placeFood(snake);
    assert.equal(f.y, G.ROWS - 1);
  }
});

test('placeFood returns null when the field is full', () => {
  const snake = [];
  for (let x = 0; x < G.COLS; x++) for (let y = 0; y < G.ROWS; y++) snake.push({ x, y });
  assert.equal(G.placeFood(snake), null);
});

// --- speed ---

test('speed increases every 10 points', () => {
  assert.equal(G.currentSpeed(0), G.BASE_SPEED);
  assert.equal(G.currentSpeed(9), G.BASE_SPEED);
  assert.equal(G.currentSpeed(10), G.BASE_SPEED - G.SPEED_STEP);
  assert.equal(G.currentSpeed(19), G.BASE_SPEED - G.SPEED_STEP);
  assert.equal(G.currentSpeed(20), G.BASE_SPEED - 2 * G.SPEED_STEP);
});

test('speed never drops below MIN_SPEED', () => {
  assert.equal(G.currentSpeed(10000), G.MIN_SPEED);
});

// --- immediate turn ---

test('shouldTurnNow is false while the snake is still sliding', () => {
  assert.equal(G.shouldTurnNow(0, 0), false);
  assert.equal(G.shouldTurnNow(G.BASE_SPEED * G.SMOOTH - 1, 0), false);
});

test('shouldTurnNow is true once the slide is finished, before the next tick', () => {
  assert.equal(G.shouldTurnNow(G.BASE_SPEED * G.SMOOTH, 0), true);
  assert.equal(G.shouldTurnNow(G.BASE_SPEED - 1, 0), true);
});

test('shouldTurnNow can fire at all (SMOOTH < 1)', () => {
  // acc is always below the step interval, so with SMOOTH = 1 the branch would be dead code
  assert.ok(G.SMOOTH < 1);
});

test('shouldTurnNow follows the speed-up', () => {
  const fast = G.currentSpeed(10) * G.SMOOTH;
  assert.equal(G.shouldTurnNow(fast, 10), true);
  assert.equal(G.shouldTurnNow(fast, 0), fast >= G.BASE_SPEED * G.SMOOTH);
});

// --- best score ---

test('best score is loaded from storage', () => {
  const st = memoryStorage({ snakeBest: '42' });
  assert.equal(G.createState({ storage: st }).best, 42);
});

test('best score is 0 if storage is empty or broken', () => {
  assert.equal(G.createState({ storage: memoryStorage() }).best, 0);
  assert.equal(G.createState({ storage: memoryStorage({ snakeBest: 'abc' }) }).best, 0);
  const broken = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); } };
  assert.equal(G.createState({ storage: broken }).best, 0);
});

test('eating beyond the best score saves a new record', () => {
  const st = memoryStorage({ snakeBest: '0' });
  const s = G.createState({ storage: st, random: () => 0 });
  s.food = { x: 11, y: 10 };
  G.step(s);
  assert.equal(s.best, 1);
  assert.equal(st.data.snakeBest, '1');
});

test('score below the record does not overwrite it', () => {
  const st = memoryStorage({ snakeBest: '5' });
  const s = G.createState({ storage: st, random: () => 0 });
  s.food = { x: 11, y: 10 };
  G.step(s);
  assert.equal(s.score, 1);
  assert.equal(s.best, 5);
  assert.equal(st.data.snakeBest, '5');
});

test('a failing storage does not break the game', () => {
  const broken = { getItem: () => null, setItem() { throw new Error('quota'); } };
  const s = G.createState({ storage: broken, random: () => 0 });
  s.food = { x: 11, y: 10 };
  assert.doesNotThrow(() => G.step(s));
  assert.equal(s.best, 1);
});
