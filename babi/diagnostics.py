from itertools import groupby
from textwrap import shorten
from typing import Optional
import curses

from babi.buf import Buf

class Diagnostics:

    def __init__(self):
        self.diagnostics: Optional[list[dict]] = None
        curses.init_pair(19, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(18, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(17, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(16, curses.COLOR_WHITE, curses.COLOR_BLACK)

    @staticmethod
    def clamp(to_clamp: int, range_min: int, range_max: int) -> int: 
        return min(max(to_clamp, range_min), range_max)

    def draw(self, screen, y_offset: int, screen_width: int, screen_height: int, buf: Buf):
        assert self.diagnostics is not None
        screen_clamped_diagnostics = filter(lambda diagnostic: int(diagnostic["range"]["start"]["line"]) in range(y_offset + 1, y_offset + screen_height), self.diagnostics["diagnostics"])
        for line_num, line_grouped_diagnostics in groupby(screen_clamped_diagnostics, lambda diagnostic: int(diagnostic["range"]["start"]["line"])):
            # Wrap the iterator in a list for access to len, ...
            line_grouped_diagnostics = list(line_grouped_diagnostics)
            # TODO sometimes this goes out of range, therefore it gets clamped, have to find out why and fix it 
            #line_num = self.clamp(line_num, 0, len(buf))
            line_length = len(buf[line_num])
            if len(line_grouped_diagnostics) == 1:
                message = line_grouped_diagnostics[0]["message"]
            else:
                message = "{diagnostic} (+{amount} more)".format(diagnostic=line_grouped_diagnostics[0]["message"], amount=(len(line_grouped_diagnostics) - 1))
            # If there is less than 5 characters space, don't even bother trying to display anything, it would be unreadable anyway
            if screen_width - line_length - 1 < 5:
                return
            # Message is too long to fit on screen, has to be truncated
            if line_length + len(message) + 1 > screen_width:
                message = shorten(message, screen_width - line_length - 1, placeholder="...")
            match line_grouped_diagnostics[0].get("severity"):
                # High severity, red color
                case 1:
                    color = curses.color_pair(19)
                # Medium severity, yellow color
                case 2:
                    color = curses.color_pair(18)
                # Low severity, green color
                case 3:
                    color = curses.color_pair(17)
                # No severity, white color
                case _:
                    color = curses.color_pair(16)
            screen.addstr(line_num - y_offset, line_length, message, color)