from dataclasses import dataclass


DIRECTIONS = (("u", (-1, 0)),("d", (1, 0)),("l", (0, -1)),("r", (0, 1)),)

@dataclass(frozen=True)
class State:
    player: tuple
    crates: frozenset

@dataclass(frozen=True)
class Transition:
    action: str
    state: State
    pushed: bool

    @property
    def cost(self):
        return 1

@dataclass(frozen=True)
class Board:
    width: int
    height: int
    walls: frozenset
    targets: frozenset

    def is_floor(self, position):
        row, column = position

        if row < 0 or row >= self.height:
            return False
        if column < 0 or column >= self.width:
            return False
        if position in self.walls:
            return False

        return True

    def is_solved(self, state):
        return state.crates == self.targets

    def move(self, state, action):
        if action == "u":
            row_change, column_change = -1, 0
        elif action == "d":
            row_change, column_change = 1, 0
        elif action == "l":
            row_change, column_change = 0, -1
        elif action == "r":
            row_change, column_change = 0, 1
        else:
            raise ValueError("Action must be one of 'u', 'd', 'l', 'r'")

        row, column = state.player
        destination = (row + row_change, column + column_change)

        if not self.is_floor(destination):
            return None

        crates = state.crates
        pushed = False

        if destination in crates:
            beyond = (
                destination[0] + row_change,
                destination[1] + column_change,
            )

            if not self.is_floor(beyond):
                return None
            if beyond in crates:
                return None

            updated_crates = set(crates)
            updated_crates.remove(destination)
            updated_crates.add(beyond)
            crates = frozenset(updated_crates)
            pushed = True

        new_state = State(destination, crates)
        return Transition(action, new_state, pushed)

    def successors(self, state):
        for action in ("u", "d", "l", "r"):
            transition = self.move(state, action)
            if transition is not None:
                yield transition

def from_arrays(width, height, mapData, itemsData):
    if type(width) is not int or type(height) is not int:
        raise ValueError("Width and height must be integers")
    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive")

    if len(mapData) != height or len(itemsData) != height:
        raise ValueError("The number of rows must match height")

    for row in mapData:
        if len(row) != width:
            raise ValueError("Every mapData row must match width")

    for row in itemsData:
        if len(row) != width:
            raise ValueError("Every itemsData row must match width")

    walls = set()
    targets = set()
    crates = set()
    players = []

    for row in range(height):
        for column in range(width):
            position = (row, column)
            tile = mapData[row][column]
            item = itemsData[row][column]

            if tile not in ("#", ".", " "):
                raise ValueError(f"Unsupported map symbol at {position}")
            if item not in ("@", "$", " "):
                raise ValueError(f"Unsupported item symbol at {position}")

            if tile == "#":
                walls.add(position)
                if item != " ":
                    raise ValueError(f"An item overlaps a wall at {position}")
            elif tile == ".":
                targets.add(position)

            if item == "$":
                crates.add(position)
            elif item == "@":
                players.append(position)

    if len(players) != 1:
        raise ValueError("A puzzle must contain exactly one player")
    if len(crates) == 0:
        raise ValueError("A puzzle must contain at least one crate")
    if len(crates) != len(targets):
        raise ValueError("The numbers of crates and targets must match")

    board = Board(width, height, frozenset(walls), frozenset(targets))
    initial_state = State(players[0], frozenset(crates))
    return board, initial_state
