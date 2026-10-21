import os
import time

try:
    from .game_logic import from_arrays
    from .sokobot import SokoBot
except ImportError:
    from game_logic import from_arrays
    from sokobot import SokoBot


def load_map(filepath):
    with open(filepath, "r") as f:
        lines = [line.rstrip("\r\n") for line in f]

    while lines and lines[-1] == "":
        lines.pop()

    height = len(lines)
    width = max(len(line) for line in lines)

    mapData = [[" " for _ in range(width)] for _ in range(height)]
    itemsData = [[" " for _ in range(width)] for _ in range(height)]

    for row in range(height):
        line = lines[row]
        for column in range(len(line)):
            ch = line[column]
            if ch == "#":
                mapData[row][column] = "#"
            elif ch == ".":
                mapData[row][column] = "."
            elif ch == "@":
                itemsData[row][column] = "@"
            elif ch == "$":
                itemsData[row][column] = "$"
            elif ch == "+":
                mapData[row][column] = "."
                itemsData[row][column] = "@"
            elif ch == "*":
                mapData[row][column] = "."
                itemsData[row][column] = "$"

    return width, height, mapData, itemsData


def check_solution(width, height, mapData, itemsData, moves):   # if the bot returns "" = failed to find a soln, checks if answers were valid
    if not moves:
        return False, 0

    board, state = from_arrays(width, height, mapData, itemsData)
    pushes = 0 # a counter to track the amount of moves

    for action in moves:
        if action not in ("u", "d", "l", "r"):
            return False, pushes
        transition = board.move(state, action)
        if transition is None:
            return False, pushes
        if transition.pushed:
            pushes += 1
        state = transition.state

    return board.is_solved(state), pushes


def main():
    maps_dir = "maps"
    if not os.path.exists(maps_dir):
        maps_dir = os.path.join("..", "..", "maps")

    files = [f for f in os.listdir(maps_dir) if f.endswith(".txt")]
    files.sort()

    bot = SokoBot()
    solved_count = 0
    rows = ["Map,Width,Height,Crates,Solved,Time,Moves,Pushes"]

    print("Map\t\tCrates\tSolved\tTime(s)\tMoves\tPushes")
    print("-" * 55)

    for filename in files:  # loop for map files
        path = os.path.join(maps_dir, filename)
        width, height, mapData, itemsData = load_map(path)
        crates = sum(row.count("$") for row in itemsData)

        start_time = time.time()
        solution = bot.solveSokobanPuzzle(width, height, mapData, itemsData)
        elapsed = time.time() - start_time

        solved, pushes = check_solution(width, height, mapData, itemsData, solution)
        if elapsed > 15.0:
            solved = False

        if solved:
            solved_count += 1

        moves_count = len(solution) if solution else 0
        print(f"{filename:<15}\t{crates}\t{solved}\t{elapsed:.4f}\t{moves_count}\t{pushes}")
        rows.append(f"{filename},{width},{height},{crates},{solved},{elapsed:.4f},{moves_count},{pushes}")

    print("-" * 55)     # generate results.csv file
    print(f"Total Solved: {solved_count}/{len(files)}")

    with open("results.csv", "w") as f:
        f.write("\n".join(rows))


if __name__ == "__main__":
    main()