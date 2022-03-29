from dataclasses import field
from functools import cache
import pygame
from enum import Enum, auto


class CellState(Enum):
    IDLE = auto()
    FLAG = auto()
    QUESTION = auto()
    BOMB = auto()
    BOMB_WRONG = auto()
    BOMB_EXPLODED = auto()
    OPEN = auto()


class Win:
    pos = [0, 0]
    _zoom = 1
    _zoom_fr = 0.1
    _zoom_range = (0.5, 5)

    def __init__(self):
        self.stack = []

    def _add(self, item):
        self.stack.append(item)

    def _remove(self, item):
        self.stack.remove(item)

    def render(self, surface: pygame.Surface):
        win_pos_x, win_pos_y = self.pos
        for item in self.stack:
            (src_pos_x, src_pos_y), src = item.get_content()
            real_pos = [
                win_pos_x + src_pos_x * self._zoom,
                win_pos_y + src_pos_y * self._zoom,
            ]
            surface.blit(src, real_pos)

    def ch_zoom(self, fr_count, pos):
        zoom = self._zoom
        delta_zoom = self._zoom_fr * fr_count
        changed_zoom = zoom + delta_zoom
        wpos = self.pos
        delta_pos = (pos[0] - wpos[0], pos[1] - wpos[1])
        if self._zoom_range[0] < changed_zoom < self._zoom_range[1]:
            self.pos[0] -= delta_pos[0] * changed_zoom / zoom - delta_pos[0]
            self.pos[1] -= delta_pos[1] * changed_zoom / zoom - delta_pos[1]
            self._zoom = changed_zoom

    @property
    def zoom(self):
        return self._zoom

    def check_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEWHEEL:
            self.ch_zoom(event.y, pygame.mouse.get_pos())


class Cell:
    _idle_figure = pygame.image.load("assets/single-files/minesweeper_00.png")
    _idle_sunken_figure = _open_figure = pygame.image.load(
        "assets/single-files/minesweeper_01.png"
    )
    _flag_figure = pygame.image.load("assets/single-files/minesweeper_02.png")
    _question_figure = pygame.image.load("assets/single-files/minesweeper_03.png")
    _question_sunken_figure = pygame.image.load(
        "assets/single-files/minesweeper_04.png"
    )
    _bomb_figure = pygame.image.load("assets/single-files/minesweeper_05.png")
    _exploded_figure = pygame.image.load("assets/single-files/minesweeper_06.png")
    _bomb_wrong_figure = pygame.image.load("assets/single-files/minesweeper_07.png")
    _number_figures = [
        pygame.image.load(f"assets/single-files/minesweeper_{i:02d}.png")
        for i in range(8, 16)
    ]
    _fig_size = _idle_figure.get_size()[0]

    def __init__(self, win, field, grid, **kwargs) -> None:
        self.win = win
        self.state = kwargs.get("state", CellState.IDLE)
        self.sunken = False
        self.origin = field.pos
        self.grid = grid
        self.pos = (
            self.origin[0] + self.grid[0] * self._fig_size,
            self.origin[1] + self.grid[1] * self._fig_size,
        )
        self.isBomb = False
        self.field = field
        self.num = 0
        self.isOpen = False
        win._add(self)

    def __del__(self):
        self.win._remove(self)

    @cache
    def get_neighbours(self):
        sgrid = self.grid[::-1]
        field = self.field
        fgrid = field.grid[::-1]
        frange = (range(fgrid[0]), range(fgrid[1]))
        data = []
        if sgrid[0] + 1 in frange[0]:
            data.append(field[sgrid[0] + 1, sgrid[1]])
            if sgrid[1] + 1 in frange[1]:
                data.append(field[sgrid[0] + 1, sgrid[1] + 1])
            if sgrid[1] > 0:
                data.append(field[sgrid[0] + 1, sgrid[1] - 1])
        if sgrid[0] > 0:
            data.append(field[sgrid[0] - 1, sgrid[1]])
            if sgrid[1] > 0:
                data.append(field[sgrid[0] - 1, sgrid[1] - 1])
        if sgrid[1] > 0:
            data.append(field[sgrid[0], sgrid[1] - 1])
        if sgrid[1] + 1 in frange[1]:
            data.append(field[sgrid[0], sgrid[1] + 1])
            if sgrid[0] > 0:
                data.append(field[sgrid[0] - 1, sgrid[1] + 1])
        return data

    def open(self):
        if self.state not in [CellState.IDLE, CellState.QUESTION]:
            return
        neighbours = self.get_neighbours()
        num = 0
        for neighbour in neighbours:
            if neighbour.isBomb:
                num += 1
        self.num = num
        self.isOpen = True
        self.state = CellState.OPEN
        if self.isBomb:
            self.state = CellState.BOMB_EXPLODED
            self.field.explode()
            return
        if not num:
            for neighbour in neighbours:
                if not neighbour.isOpen:
                    neighbour.open()

    def reveal(self):
        if self.isBomb:
            if self.state not in [CellState.FLAG, CellState.BOMB_EXPLODED]:
                self.state = CellState.BOMB
        if self.state == CellState.FLAG:
            if not self.isBomb:
                self.state = CellState.BOMB_WRONG

    def get_content(self):
        if self.state == CellState.IDLE:
            if self.sunken:
                fig = self._idle_sunken_figure
            else:
                fig = self._idle_figure
        elif self.state == CellState.FLAG:
            fig = self._flag_figure
        elif self.state == CellState.QUESTION:
            if self.sunken:
                fig = self._question_sunken_figure
            else:
                fig = self._question_figure
        elif self.state == CellState.BOMB:
            fig = self._bomb_figure
        elif self.state == CellState.BOMB_EXPLODED:
            fig = self._exploded_figure
        elif self.state == CellState.BOMB_WRONG:
            fig = self._bomb_wrong_figure
        elif self.state == CellState.OPEN:
            if self.num == 0:
                fig = self._open_figure
            else:
                fig = self._number_figures[self.num - 1]
        return (
            self.pos,
            pygame.transform.scale(fig, (self._fig_size * self.win.zoom,) * 2),
        )

    def click_down(self, btn):
        if btn == pygame.BUTTON_LEFT:
            if self.state in [CellState.IDLE, CellState.QUESTION]:
                self.sunken = True

    def click_up(self, btn):
        if btn == pygame.BUTTON_LEFT:
            self.sunken = False

    def click_complete(self, btn):
        if btn == pygame.BUTTON_RIGHT:
            match self.state:
                case CellState.IDLE:
                    self.state = CellState.FLAG
                case CellState.FLAG:
                    self.state = CellState.QUESTION
                case CellState.QUESTION:
                    self.state = CellState.IDLE
        if btn == pygame.BUTTON_LEFT:
            self.open()

    def __str__(self) -> str:
        return str(self.grid)

    def __repr__(self) -> str:
        return str(self)


class Field:
    last_keydown = None
    _finished = False

    def __init__(self, win, pos, grid):
        self.pos = pos
        self.win = win
        self.grid = grid
        self.cells = [
            [Cell(win, self, (i, j)) for i in range(grid[0])] for j in range(grid[1])
        ]
        self.cell_size = self.cells[0][0]._fig_size

    def explode(self):
        self._finished = True
        for row in self.cells:
            for cell in row:
                cell.reveal()

    def mouse_over(self, pos):
        w_pos_x, w_pos_y = self.win.pos
        f_pos_x, f_pos_y = self.pos
        zoom = self.win.zoom
        return (
            w_pos_x + f_pos_x * zoom
            < pos[0]
            < w_pos_x + (f_pos_x + self.grid[0] * self.cell_size) * zoom
            and w_pos_y + f_pos_y * zoom
            < pos[1]
            < w_pos_y + (f_pos_y + self.grid[1] * self.cell_size) * zoom
        )

    def get_grid(self, pos):
        w_pos_x, w_pos_y = self.win.pos
        f_pos_x, f_pos_y = self.pos
        zoom = self.win.zoom
        x = int((((pos[0] - w_pos_x) / self.win.zoom) - f_pos_x) / self.cell_size)
        y = int((((pos[1] - w_pos_y) / self.win.zoom) - f_pos_y) / self.cell_size)
        return y, x

    def handle_mouse_click_down(self, pos, btn):
        if self.mouse_over(pos):
            grid = self.get_grid(pos)
            self[grid].click_down(btn)
            self.last_keydown = grid

    def handle_mouse_click_up(self, pos, btn):
        last_keydown = self.last_keydown
        if last_keydown:
            self[last_keydown].click_up(btn)
        if self.mouse_over(pos):
            grid = self.get_grid(pos)
            if last_keydown == grid:
                self[grid].click_complete(btn)
            self.last_keydown = None

    def check_event(self, event: pygame.event.Event):
        if self._finished:
            return
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.handle_mouse_click_down(event.pos, event.button)
        elif event.type == pygame.MOUSEBUTTONUP:
            self.handle_mouse_click_up(event.pos, event.button)

    def __getitem__(self, key):
        return self.cells[key[0]][key[1]]
