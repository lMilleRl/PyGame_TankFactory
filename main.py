from enum import Enum

import pygame

from tank_factory.constants import APP_TITLE, FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from tank_factory.entities import FactoryStatus
from tank_factory.factory import Factory
from tank_factory.renderer import Renderer


class ScreenState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    VICTORY = "victory"


MOVEMENT_KEYS = {
    pygame.K_UP: (0, -1),
    pygame.K_DOWN: (0, 1),
    pygame.K_LEFT: (-1, 0),
    pygame.K_RIGHT: (1, 0),
}


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(APP_TITLE)
    clock = pygame.time.Clock()
    renderer = Renderer()
    factory = Factory()
    screen_state = ScreenState.MENU
    running = True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif screen_state is ScreenState.MENU:
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            factory = Factory()
                            screen_state = ScreenState.PLAYING
                    elif screen_state is ScreenState.PLAYING:
                        if event.key in MOVEMENT_KEYS:
                            factory.move_drone(*MOVEMENT_KEYS[event.key])
                        elif event.key == pygame.K_SPACE:
                            factory.interact()
                        elif event.key == pygame.K_r:
                            factory = Factory()
                        elif event.key == pygame.K_m:
                            screen_state = ScreenState.MENU

                        if factory.status is FactoryStatus.WON:
                            screen_state = ScreenState.VICTORY
                    elif screen_state is ScreenState.VICTORY:
                        if event.key in (pygame.K_RETURN, pygame.K_r):
                            factory = Factory()
                            screen_state = ScreenState.PLAYING
                        elif event.key == pygame.K_m:
                            screen_state = ScreenState.MENU

            if screen_state is ScreenState.MENU:
                renderer.draw_menu(screen)
            elif screen_state is ScreenState.PLAYING:
                renderer.draw_game(screen, factory)
            else:
                renderer.draw_victory(screen, factory)

            pygame.display.flip()
            clock.tick(FPS)
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
