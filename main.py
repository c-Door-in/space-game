import time
import asyncio
import curses
import random
from itertools import cycle
from statistics import median

from environs import Env

from curses_tools import draw_frame, read_controls, get_frame_size


async def blink(canvas, row, column, symbol='*'):

    while True:
        for _ in range(random.randint(0, 3)):
            await asyncio.sleep(0)
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def check_border_touch(top_row, left_column, max_row, max_column, frame_rows, frame_columns):

    top_row = 1 if top_row < 1 else top_row
    left_column = 1 if left_column < 1 else left_column
    top_row = max_row - frame_rows if top_row + frame_rows > max_row else top_row
    left_column = max_column - frame_columns \
        if left_column + frame_columns > max_column else left_column
    return top_row, left_column


async def animate_spaceship(canvas, frames, max_row, max_column, speed=1):

    canvas.nodelay(True)
    
    ship_rows = max([get_frame_size(frame)[0] for frame in frames])
    ship_columns = max([get_frame_size(frame)[1] for frame in frames])

    middle_row = median([1, (max_row)])
    middle_column = median([1, (max_column)])
    top_row = middle_row - median([0, ship_rows])
    left_column = middle_column - median([0, ship_columns])
    
    for frame in cycle(frames):
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        if rows_direction:
            top_row += rows_direction * speed
        if columns_direction:
            left_column += columns_direction * speed

        top_row, left_column = check_border_touch(top_row,
                                                  left_column,
                                                  max_row,
                                                  max_column,
                                                  ship_rows,
                                                  ship_columns)
        
        draw_frame(canvas, round(top_row), round(left_column), frame)
        canvas.refresh()
        await asyncio.sleep(0)
        draw_frame(canvas, round(top_row), round(left_column), frame, negative=True)
        canvas.refresh()


def get_rocket_frames():

    with open('animations/rocket_frame_1.txt', 'r') as file:
        rocket_frame_1 = file.read()
    with open('animations/rocket_frame_2.txt', 'r') as file:
        rocket_frame_2 = file.read()

    return rocket_frame_1, rocket_frame_2


def draw(canvas, tick_timeout, star_simbols, stars_amount, spaceship_speed):
    
    curses.curs_set(False)
    row, column = canvas.getmaxyx()
    max_row, max_column = row - 1, column - 1

    coroutines = []
    for _ in range(stars_amount):
        row = random.randint(1, max_row)
        column = random.randint(1, max_column)
        simbol = random.choice(star_simbols)
        coroutines.append(blink(canvas, row, column, simbol))

    frames = get_rocket_frames()
    spaceship = animate_spaceship(canvas, frames, max_row, max_column, spaceship_speed)
    coroutines.append(spaceship)

    while True:
        for coroutine in coroutines.copy():
            try:
                canvas.border()
                coroutine.send(None)
                canvas.refresh()
            except StopIteration:
                coroutines.remove(coroutine)
        time.sleep(tick_timeout)


def main(canvas):
    env = Env()
    env.read_env()

    tick_timeout=env.float('TICK_TIMEOUNT', 0.1)
    star_simbols = env.str('STAR_SIMBOLS', '+*.:')
    stars_amount=env.int('STARS_AMOUNT', 200)
    spaceship_speed = env.float('SPACESHIP_SPEED', 10.0)

    draw(canvas, tick_timeout, star_simbols, stars_amount, spaceship_speed)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(main)
