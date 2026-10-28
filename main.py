from enum import Enum
from pathlib import Path

import pygame

from tank_factory.constants import APP_TITLE, FPS, WINDOW_HEIGHT, WINDOW_WIDTH
from tank_factory.entities import FactoryStatus
from tank_factory.factory import Factory
from tank_factory.persistence import (
    DEFAULT_SAVE_PATH,
    append_score,
    load_factory_save,
    save_factory,
    setup_game_logging,
)
from tank_factory.renderer import Renderer

PROJECT_ROOT = Path(__file__).resolve().parent


class ScreenState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    VICTORY = "victory"
    NAME_INPUT = "name_input"


MOVEMENT_KEYS = {
    pygame.K_UP: (0, -1),
    pygame.K_DOWN: (0, 1),
    pygame.K_LEFT: (-1, 0),
    pygame.K_RIGHT: (1, 0),
}


def main() -> None:
    logger = setup_game_logging()
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(APP_TITLE)
    clock = pygame.time.Clock()
    renderer = Renderer()
    factory = Factory.create_for_game()
    logger.info("Старт игры: %s", factory.message)
    screen_state = ScreenState.MENU
    player_name = ""
    score_saved = False
    status_hint = ""
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
                            factory = Factory.create_for_game()
                            score_saved = False
                            player_name = ""
                            status_hint = ""
                            logger.info("Новая сессия. %s", factory.message)
                            screen_state = ScreenState.PLAYING
                    elif screen_state is ScreenState.PLAYING:
                        if event.key in MOVEMENT_KEYS:
                            moved = factory.move_drone(*MOVEMENT_KEYS[event.key])
                            if moved:
                                logger.info("Шаг %s: дрон -> %s", factory.turn_count, factory.drone_position)
                        elif event.key == pygame.K_SPACE:
                            before = len(factory.assembly_stack)
                            if factory.interact() and len(factory.assembly_stack) > before:
                                logger.info(
                                    "Сборка: установлено %s, стек=%s",
                                    factory.assembly_stack[-1].name,
                                    factory.assembly_indices,
                                )
                        elif event.key == pygame.K_r:
                            factory = Factory.create_for_game()
                            score_saved = False
                            status_hint = ""
                            logger.info("Перезапуск сессии")
                        elif event.key == pygame.K_m:
                            screen_state = ScreenState.MENU
                        elif event.key == pygame.K_F5:
                            save_path = save_factory(factory)
                            status_hint = f"Сохранено: {save_path.name}"
                            factory.message = status_hint
                            logger.info("Сохранение в %s (ход %s)", save_path.name, factory.turn_count)
                        elif event.key == pygame.K_F9:
                            try:
                                load_factory_save(factory)
                                status_hint = f"Загружено: {DEFAULT_SAVE_PATH.name}"
                                factory.message = status_hint
                                logger.info("Загрузка сохранения, ход %s", factory.turn_count)
                            except FileNotFoundError:
                                status_hint = "Файл сохранения не найден"
                                factory.message = status_hint
                            except (ValueError, KeyError, TypeError, OSError) as exc:
                                status_hint = f"Повреждённое сохранение: {exc}"
                                factory.message = status_hint
                                logger.warning("Ошибка загрузки: %s", exc)

                        if factory.status is FactoryStatus.WON:
                            logger.info("Победа за %s ходов", factory.turn_count)
                            screen_state = ScreenState.NAME_INPUT
                            player_name = ""
                            score_saved = False
                    elif screen_state is ScreenState.NAME_INPUT:
                        if event.key == pygame.K_RETURN:
                            if player_name.strip():
                                append_score(player_name, factory.turn_count, len(factory.assembly_stack))
                                score_saved = True
                                logger.info("Рекорд: %s, ходов=%s", player_name.strip(), factory.turn_count)
                                screen_state = ScreenState.VICTORY
                            else:
                                status_hint = "Введите имя перед сохранением рекорда"
                        elif event.key == pygame.K_BACKSPACE:
                            player_name = player_name[:-1]
                        elif event.key == pygame.K_m:
                            screen_state = ScreenState.MENU
                        else:
                            char = event.unicode
                            if char and char.isprintable() and len(player_name) < 24:
                                player_name += char
                    elif screen_state is ScreenState.VICTORY:
                        if event.key in (pygame.K_RETURN, pygame.K_r):
                            factory = Factory.create_for_game()
                            score_saved = False
                            player_name = ""
                            status_hint = ""
                            screen_state = ScreenState.PLAYING
                        elif event.key == pygame.K_m:
                            screen_state = ScreenState.MENU

            if screen_state is ScreenState.MENU:
                renderer.draw_menu(screen)
            elif screen_state is ScreenState.PLAYING:
                renderer.draw_game(screen, factory)
            elif screen_state is ScreenState.NAME_INPUT:
                renderer.draw_name_input(screen, factory, player_name, status_hint)
            else:
                renderer.draw_victory(screen, factory, player_name if score_saved else "")

            pygame.display.flip()
            clock.tick(FPS)
    finally:
        logger.info("Выход из игры")
        pygame.quit()


if __name__ == "__main__":
    main()
