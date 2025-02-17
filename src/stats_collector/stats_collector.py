# SPDX-FileCopyrightText: 2025-present Bogatyrev Aleksandr <bogatirevas.dev@gmail.com>

"""
Statistics collector for displaying it in the console as a table
"""

import os
import copy
from typing import TypedDict, Unpack, Literal
from operator import getitem
from dataclasses import dataclass


ESC_CODE_CPL = "\033[F"  # Cursor Previous Line
ESC_CODE_EL = "\033[K"  # Erase in Line
default_terminal_columns = 160


def delete_console_line():
    print(f"{ESC_CODE_CPL}{ESC_CODE_EL}", end="")


def get_terminal_columns():
    try:
        columns = os.get_terminal_size().columns
    except Exception as exc:
        columns = default_terminal_columns
    return columns


def limit_console_line(text, limit=None):
    limit = get_terminal_columns() if limit is None else limit
    return text[0:limit]


class ResetTableMode:
    TERMINAL_CHANGE = "terminal_change"
    TERMINAL_DECREASE = "terminal_decrease"
    TABLE_DECREASE = "table_decrease"


class _StatsCollectorConfigKwargs(TypedDict, total=False):
    can_print_title: bool
    is_short_format: bool
    can_print_stats: bool
    can_write_file: bool
    file_mode: str
    file: str
    reset_table_mode: Literal["terminal_change", "terminal_decrease", "table_decrease"]


class StatsCollectorConfig:
    can_print_title: bool = True
    is_short_format: bool = True
    can_print_stats: bool = True
    can_write_file: bool = False
    file_mode: str = "w"
    file: str = "statistics.log"
    reset_table_mode: str = ResetTableMode.TABLE_DECREASE

    def __init__(self, **kwargs: Unpack[_StatsCollectorConfigKwargs]):
        for k, v in kwargs.items():
            if hasattr(self, k):
                self.__setattr__(k, v)


@dataclass
class StatsCollectorTable:
    should_update_headers: bool = False
    should_update_title: bool = False
    title_str: str = ""
    headers_str: str = ""
    stats_str: str = ""
    title_len: int = 0
    headers_len: int = 0
    stats_len: int = 0
    info_len: int = 0
    line_limit: int = 0
    title_width: int = 0
    table_width: int = 0
    max_stat_width: int = 0


class StatsCollector:
    def __init__(self, headers: list | dict, title: str | None = "STATISTICS",
                 **kwargs: Unpack[_StatsCollectorConfigKwargs]):
        self._conf = StatsCollectorConfig(**kwargs)
        if self._should_rewrite_file():
            if os.path.exists(self._conf.file):
                os.remove(self._conf.file)
        self._table = StatsCollectorTable()
        self._title = ""
        self._headers = {}
        self._stats = []
        self._last_stat = {}
        self._references = {}
        self._set_headers(headers)
        self.set_title(title)

    def _set_headers(self, headers: list | dict):
        headers_dict = {}
        if isinstance(headers, list):
            for index, name in enumerate(headers):
                headers_dict[name] = {"index": index,
                                      "name": name,
                                      "minlen": len(name)}
        elif isinstance(headers, dict):
            for index, (key, name) in enumerate(headers.items()):
                headers_dict[key] = {"index": index,
                                     "name": name,
                                     "minlen": len(name)}
        self._headers = headers_dict
        return self.headers

    def _reset_table(self, reason: str = None, should_print_text=True):
        """
        If errors occur, the table is reset
        and continues writing as a new table to output
        error message and maintain table integrity in the console
        """
        text = ""
        self._table = StatsCollectorTable()
        text = "Reset table"
        if should_print_text:
            if text != "":
                text = f'{text}: '
            if reason is not None:
                text = f"{text}{reason}"
            print(text)

    def rename_headers(self, headers: dict):
        temp_headers = copy.deepcopy(self.headers)
        for key, name in headers.items():
            header = temp_headers.get(key)
            if header is None:
                self._reset_table(f'Wrong header key "{key}"')
                return False
            temp_headers[key]["name"] = name
            minlen = len(name)
            if minlen > header["minlen"]:
                temp_headers[key]["minlen"] = minlen
        self._headers = temp_headers
        self._table.should_update_headers = True
        return self.headers

    def set_title(self, title: str | None):
        if title is None:
            title = ""
        self._title = title
        self._table.should_update_title = True
        return self.title

    def _print_str(self, cur_str: str):
        print(cur_str)
        self._write_str_to_file(cur_str)

    def _write_str_to_file(self, cur_str: str):
        if self._conf.can_write_file:
            with open(self._conf.file, "a") as f:
                f.write(f"{cur_str}\n")

    def _print_title(self):
        if self._conf.can_print_title and (self._table.title_len == 0) and (self.title != ""):
            title_str = f'| {self.title} |'
            self._table.table_width = len(title_str)
            title_str = limit_console_line(title_str, self._table.line_limit)
            line = "-" * len(title_str)
            temp_str = f'{line}\n{title_str}'
            self._table.title_str = temp_str
            self._table.title_len = 1
            self._table.should_update_title = False
            self._print_str(self._table.title_str)
        return self._table.title_str

    def _print_headers(self):
        if self._table.headers_len == 0:
            header_str = "|"
            for key, header in self.headers.items():
                index, name, minlen = header["index"], header["name"], header["minlen"]
                header_str = f'{header_str} {name:{minlen}} |'

            self._table.table_width = len(header_str)
            header_str = limit_console_line(header_str, self._table.line_limit)
            line = "-" * len(header_str)
            header_title_line = limit_console_line(
                "-" * max(self._table.table_width, self._table.title_width),
                self._table.line_limit
            )
            temp_str = f'{header_title_line}\n{header_str}\n{line}'
            self._table.headers_str = temp_str
            self._table.headers_len = 1
            self._table.should_update_headers = False
            self._print_str(self._table.headers_str)
        return self._table.headers_str

    def _print_stat(self):
        stat_str = "|"
        for key, header in self.headers.items():
            index, name, minlen = header["index"], header["name"], header["minlen"]
            value = self._last_stat[index]
            stat_str = f'{stat_str} {value:{minlen}} |'

        stat_str = limit_console_line(stat_str, self._table.line_limit)
        self._table.max_stat_width = len(stat_str)
        line = "-" * len(stat_str)
        temp_str = f'{stat_str}\n{line}'
        info = self._last_stat.get("info", [])
        if len(info) > 0:
            info_str = ""
            for info_item in info:
                if len(info_item) > self._table.max_stat_width:
                    self._table.max_stat_width = len(info_item)
                info_str = f'{info_str}{limit_console_line(info_item, self._table.line_limit)}\n'
            temp_str = f'{temp_str}\n{info_str}{line}'

        self._table.info_len = len(info)
        self._table.stats_str = temp_str
        self._table.stats_len = 1
        self._print_str(self._table.stats_str)
        return self._table.stats_str

    def _clear_console(self):
        count_del_lines = 0
        if self._conf.is_short_format:
            count_del_lines += (1 + self._table.stats_len) if (self._table.stats_len > 0) else 0
            count_del_lines += (1 + self._table.info_len) if (self._table.info_len > 0) else 0
            self._table.stats_len = 0
            self._table.info_len = 0
            if self._table.should_update_title and (self._table.title_len > 0):
                count_del_lines += 1 + self._table.title_len
                self._table.title_len = 0
            if (self._table.should_update_headers or self._table.should_update_title) and (self._table.headers_len > 0):
                count_del_lines += 2 + self._table.headers_len
                self._table.headers_len = 0
            for i in range(count_del_lines):
                delete_console_line()
        return count_del_lines

    def _should_reset_table(self, line_limit):
        if self._conf.reset_table_mode == ResetTableMode.TERMINAL_DECREASE:
            return line_limit < self._table.line_limit
        elif self._conf.reset_table_mode == ResetTableMode.TABLE_DECREASE:
            return line_limit < self._table.max_stat_width
        return line_limit != self._table.line_limit

    def _print_table(self):
        if self._conf.can_print_stats:
            line_limit = get_terminal_columns()
            if self._should_reset_table(line_limit):
                self._reset_table(reason=None, should_print_text=False)
            elif self._table.title_width > self._table.line_limit:
                self._table.should_update_title = True
            elif self._table.table_width > self._table.line_limit:
                self._table.should_update_headers = True

            self._table.line_limit = line_limit
            self._clear_console()
            self._print_title()
            self._print_headers()
            self._print_stat()
        return self._conf.can_print_stats

    def _delete_table(self):
        self._table.should_update_title = True
        self._table.should_update_headers = True
        self._clear_console()

    def _resize(self, stat: dict, should_update_headers=True):
        temp_stat = {}
        for key, value in stat.items():
            header = self.headers.get(key)
            if header is None:
                self._reset_table(f'Wrong stat key "{key}"')
                return False
            index = header["index"]
            temp_stat[index] = str(value)
            minlen = len(temp_stat[index])
            if minlen > header["minlen"]:
                self.headers[key]["minlen"] = minlen
                if should_update_headers:
                    self._table.should_update_headers = True
        return temp_stat

    def resize_table_by_stat(self, stat: dict):
        self._resize(stat, False)

    def _should_rewrite_file(self):
        return self._conf.can_write_file and self._conf.file_mode == "w"

    def _rewrite_file(self):
        if self._should_rewrite_file():
            self.write_to_file(self._conf.file)

    def add(self, stat: dict = None):
        self._rewrite_file()

        stat = self._write_references_to_stat(stat)

        info = stat.pop("info", "")
        if len(stat) != len(self.headers):
            self._reset_table(f'Incorrect stat quantity ({len(stat)} != {len(self.headers)})')
            return False

        temp_stat = self._resize(stat)
        if temp_stat is False:
            return False

        temp_stat["info"] = []
        if info != "":
            temp_stat["info"].append(info)

        self._last_stat = temp_stat
        self._stats.append(self._last_stat)
        self._print_table()
        return self._last_stat

    def update(self, stat: dict = None):
        if len(self._last_stat) == 0:
            self._reset_table("No stat available")
            return False

        stat = self._write_references_to_stat(stat)

        info = stat.pop("info", "")
        if len(stat) > len(self.headers):
            self._reset_table(f'Incorrect stat quantity ({len(stat)} > {len(self.headers)})')
            return False

        temp_stat2 = self._resize(stat)
        if temp_stat2 is False:
            return False

        temp_stat = copy.deepcopy(self._last_stat)
        if info != "":
            temp_stat["info"].append(info)
        temp_stat.update(temp_stat2)

        self._last_stat = temp_stat
        self._stats[-1] = self._last_stat
        self._print_table()
        return self._last_stat

    def get_table(self, should_show_table=False, is_last_stat=False, should_delete_table=False):
        stats_table = ""
        title_str = ""
        if self._conf.can_print_title and (self.title != ""):
            title_str = f'| {self.title} |'
            line = "-" * len(title_str)
            temp_str = f'{line}\n{title_str}\n'
            stats_table = temp_str

        header_str = "|"
        for key, header in self.headers.items():
            index, name, minlen = header["index"], header["name"], header["minlen"]
            header_str = f'{header_str} {name:{minlen}} |'
        line = "-" * len(header_str)
        header_title_line = "-" * max(len(header_str), len(title_str))
        temp_str = f'{header_title_line}\n{header_str}\n{line}'
        stats_table = f'{stats_table}{temp_str}'

        stats = [self._last_stat] if is_last_stat else self._stats
        for stat in stats:
            stat_str = "|"
            for key, header in self.headers.items():
                index, name, minlen = header["index"], header["name"], header["minlen"]
                value = stat[index]
                stat_str = f'{stat_str} {value:{minlen}} |'
            temp_str = f'{stat_str}\n{line}'
            info = stat.get("info", [])
            if len(info) > 0:
                info_str = "\n".join(info)
                temp_str = f'{temp_str}\n{info_str}\n{line}'
            stats_table = f'{stats_table}\n{temp_str}'

        if should_show_table:
            if should_delete_table:
                self._delete_table()
            print(stats_table)
        return stats_table

    @property
    def title(self):
        return self._title

    @property
    def headers(self):
        return self._headers

    @property
    def stats(self):
        return self._stats

    @property
    def last_stat(self):
        return self._last_stat

    def write_to_file(self, file: str, mode="w", is_last_stat=False):
        stats_table = self.get_table(should_show_table=False, is_last_stat=is_last_stat)
        stats_table = f'{stats_table}\n'
        with open(file, mode) as f:
            f.write(stats_table)
        return file

    def print_params(self):
        temp = {
            "title": self.title,
            "headers": self.headers
        }
        for key, value in temp.items():
            print(f"{key}: {value}")
        return None

    def create_reference(self, header: str, obj: object | dict | list, prop: str | int, force: bool = False):
        """
        Simulates a reference to an object field

        :param obj: mutable object
        :param prop: property or key
        :param header: header key
        :param force: if True, rewrite existing reference
        """
        if self.headers.get(header) is None:
            raise AttributeError("Wrong header key")
        if self._references.get(header) is not None and not force:
            raise AttributeError("Header key is exists")
        get_func = getitem if isinstance(obj, dict | list) else getattr
        self._references[header] = (obj, prop, get_func)

    def _write_references_to_stat(self, stat: dict = None):
        if len(self._references) > 0:
            if stat is None:
                stat = {}
            for header, (obj, prop, get_func) in self._references.items():
                if stat.get(header) is None:
                    stat[header] = get_func(obj, prop)
        return stat


if __name__ == "__main__":
    stats = StatsCollector(["h1", "h2", "h3", "h4", "h5"])
    data = [
        {"h1": 1, "h2": 1, "h3": 1, "h4": 1, "h5": 1},
        {"h1": 2, "h2": 20, "h3": 200, "h4": 2000, "h5": 20000},
        {"h1": 3, "h2": 300, "h3": 3000, "h4": 30000, "h5": 300000}
    ]
    for stat in data:
        stats.add(stat)
    stats.get_table(should_show_table=True)
