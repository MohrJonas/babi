from typing import Optional

from babi.lsp import LSPClient
import curses


class AutoComplete:

    def __init__(self) -> None:
        self.active: bool = False
        self.activation_position: Optional[tuple[int, int]] = None
        self.suggestions: Optional[list[dict]] = None
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
        #print(max(0, self.selected_suggestion_index - suggestion_display_amount))
        #print(min(len(self.suggestions), self.selected_suggestion_index + suggestion_display_amount))
        #print(self.suggestions[max(0, self.selected_suggestion_index - suggestion_display_amount):min(len(self.suggestions) - 1, self.selected_suggestion_index + suggestion_display_amount)])
        for index, suggestion in enumerate(self.suggestions[max(0, self.selected_suggestion_index - suggestion_display_amount):min(len(self.suggestions), self.selected_suggestion_index + suggestion_display_amount)]):
            text = suggestion["label"][:screen_width - len(suggestion["label"]) - 1]
            if show_above:
                if index == 0:
                    screen.addstr(position[0] - 2 - index, position[0], text, curses.color_pair(20))
                else:
                    screen.addstr(position[0] - 2 - index, position[0], text, curses.A_REVERSE)
            else:
                if index == 0:
                    screen.addstr(position[0] + 2 + index, position[0], text, curses.color_pair(20))
                else:
                    screen.addstr(position[0] + 2 + index, position[0], text, curses.A_REVERSE)
