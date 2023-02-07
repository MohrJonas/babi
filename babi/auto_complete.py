from __future__ import annotations

import curses
from textwrap import shorten
from typing import Optional

from babi.lsp import LSPClient


class AutoComplete:

    def __init__(self) -> None:
        self.active: bool = False
        self.activation_position: tuple[int, int] | None = None
        self.suggestions: list[dict] | None = None
        self.selected_suggestion_index: int = 0
        curses.init_pair(20, curses.COLOR_WHITE, curses.COLOR_CYAN)

    def get_selected_suggestion(self) -> dict:
        assert self.suggestions is not None and self.active
        return self.suggestions[self.selected_suggestion_index]

    def start_completion(self, position: tuple[int, int]) -> None:
        assert not self.active
        self.active = True
        self.activation_position = position

    def fetch_suggestions(self, lsp: LSPClient) -> None:
        lsp.get_autocompletion(self.activation_position[1], self.activation_position[0])

    def select_next_suggestion(self) -> None:
        self.selected_suggestion_index += 1
        if (self.selected_suggestion_index == len(self.suggestions)):
            self.selected_suggestion_index = 0

    def select_prev_suggestion(self) -> None:
        self.selected_suggestion_index -= 1
        if (self.selected_suggestion_index == -1):
            self.selected_suggestion_index = len(self.suggestions) - 1

    def stop_completion(self) -> None:
        assert self.active
        self.active = False
        self.activation_position = None
        self.suggestions = None

    def display(self, position: tuple[int, int], screen, screen_width: int, screen_height: int) -> None:
        assert self.suggestions is not None and self.active
        show_above = position[0] > int(screen_height / 2)
        suggestion_display_amount = min(len(self.suggestions), int(screen_height / 2) - 2)
        for index, suggestion in enumerate(self.suggestions[max(0, self.selected_suggestion_index - suggestion_display_amount):min(len(self.suggestions), self.selected_suggestion_index + suggestion_display_amount)]):
            text = suggestion['label']
            if len(text) + position[1] > screen_width - 1:
                text = shorten(text, screen_width - 1 - position[1], placeholder="...")
            if show_above:
                if index == 0:
                    screen.addstr(position[0] - 1 - index, position[0], text, curses.color_pair(20))
                else:
                    screen.addstr(position[0] - 1 - index, position[0], text, curses.A_REVERSE)
            else:
                if index == 0:
                    screen.addstr(position[0] + 1 + index, position[0], text, curses.color_pair(20))
                else:
                    screen.addstr(position[0] + 1 + index, position[0], text, curses.A_REVERSE)
