"""Snake with pygame: drawing and keyboard input. The rules live in game.py."""
import pygame

import game as G

CELL = 20
SIZE = G.COLS * CELL
HUD = 40
BG = (24, 24, 28)
FOOD = (217, 119, 87)
TEXT = (230, 230, 230)

SKINS = [
    ("Green", (143, 209, 143), (90, 166, 90)),
    ("Blue", (127, 184, 255), (74, 134, 212)),
    ("Purple", (201, 160, 255), (149, 102, 214)),
    ("Pink", (255, 158, 200), (217, 102, 154)),
    ("Yellow", (255, 226, 122), (217, 184, 58)),
    ("White", (255, 255, 255), (189, 189, 189)),
]

# Russian letters have no pygame key constants, so use the typed character
def key_char(event):
    return event.unicode.lower() if event.unicode else ""


def draw_text(screen, font, text, center, color=TEXT):
    img = font.render(text, True, color)
    screen.blit(img, img.get_rect(center=center))


def draw_game(screen, state, skin):
    screen.fill(BG)
    _, head_color, body_color = skin
    if state.food:
        fx, fy = state.food
        pygame.draw.circle(screen, FOOD, (fx * CELL + CELL // 2, HUD + fy * CELL + CELL // 2), CELL // 2 - 1)
    for i, (x, y) in enumerate(state.snake):
        color = head_color if i == 0 else body_color
        pygame.draw.rect(screen, color, (x * CELL + 1, HUD + y * CELL + 1, CELL - 2, CELL - 2))


def main():
    pygame.init()
    screen = pygame.display.set_mode((SIZE, SIZE + HUD))
    pygame.display.set_caption("Snake")
    font = pygame.font.Font(None, 28)
    big = pygame.font.Font(None, 56)
    clock = pygame.time.Clock()

    skin_index = 0
    state = G.create_state(best_path=G.BEST_FILE)
    acc = 0

    def step():
        G.step(state)

    running = True
    while running:
        dt = min(clock.tick(60), 100)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                ch = key_char(event)
                if not state.alive:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        state = G.create_state(best_path=G.BEST_FILE)
                        acc = 0
                    elif pygame.K_1 <= event.key < pygame.K_1 + len(SKINS):
                        skin_index = event.key - pygame.K_1
                    continue
                d = G.key_to_direction(ch)
                # the snake has already finished sliding: turn right now instead of waiting for the next tick
                if d and G.queue_direction(state, d) and len(state.input_queue) == 1 \
                        and G.should_turn_now(acc, state.score):
                    acc = 0
                    step()

        if state.alive:
            acc += dt
            interval = G.current_speed(state.score)
            while state.alive and acc >= interval:
                acc -= interval
                step()

        draw_game(screen, state, SKINS[skin_index])
        draw_text(screen, font, f"Score: {state.score}", (70, HUD // 2))
        draw_text(screen, font, f"Best: {state.best}", (SIZE - 70, HUD // 2))
        if not state.alive:
            draw_text(screen, big, "YOU WIN!" if state.won else "GAME OVER", (SIZE // 2, HUD + SIZE // 2 - 40))
            draw_text(screen, font, f"Score: {state.score}", (SIZE // 2, HUD + SIZE // 2))
            draw_text(screen, font, f"Skin (1-{len(SKINS)}): {SKINS[skin_index][0]}", (SIZE // 2, HUD + SIZE // 2 + 30))
            draw_text(screen, font, "Space or Enter to play again", (SIZE // 2, HUD + SIZE // 2 + 60))
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
