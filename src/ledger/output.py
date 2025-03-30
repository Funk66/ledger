from typing import Any, Sequence

import colorful


class Table:
    # TODO: add carets for sorting

    def __init__(
        self,
        columns: Sequence[str],
        data: Sequence[Sequence[Any]],
        sorting=None,
    ):
        self.size = len(columns)
        self.columns = columns
        self.data = data
        self.widths = [len(column) for column in columns]
        for row in data:
            for i in range(len(row)):
                if isinstance(row[i], float):
                    value = f"{row[i]:.2f}"
                else:
                    value = str(row[i])
                self.widths[i] = max(len(value), self.widths[i])

    def _border_(self, position: int) -> str:
        if position == 1:
            char = ("┌", "┬", "┐")
        elif position == 2:
            char = ("├", "┼", "┤")
        elif position == 3:
            char = ("└", "┴", "┘")
        else:
            ValueError(f"{position} is not a valid border position")
        return self._row_([""] * self.size, char[0], char[1], char[2], "─")

    def _row_(
        self,
        row: Sequence[Any],
        left: str = "│",
        middle: str = "│",
        right: str = "│",
        fill: str = " ",
        bold: bool = False,
        odd: int = 0,
    ) -> str:
        columns = []
        for index in range(self.size):
            value = row[index]
            if isinstance(value, int):
                cell = str(value).rjust(self.widths[index], fill)
                value = colorful.cyan(cell)
            elif isinstance(value, float):
                cell = f"{value:.2f}".rjust(self.widths[index], fill)
                value = (colorful.green if value > 0 else colorful.red)(cell)
            else:
                value = str(value).ljust(self.widths[index], fill)
            columns.append(fill + value + fill)
        middle = middle.join(columns)
        if odd:
            middle = colorful.on_black(middle)
        return left + middle + right

    def header(self) -> str:
        lines = [
            self._border_(1),
            self._row_(self.columns),
            self._border_(2),
        ]
        return "\n".join(lines)

    def rows(self) -> str:
        data = [self._row_(self.data[i], odd=i % 2) for i in range(len(self.data))]
        return "\n".join(data + [self._border_(3)])


colorful.use_16_ansi_colors()
