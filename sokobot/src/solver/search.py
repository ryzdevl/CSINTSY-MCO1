import heapq
import time
from collections import deque
from itertools import count

try:
    from .game_logic import DIRECTIONS, State, from_arrays
except ImportError:
    from game_logic import DIRECTIONS, State, from_arrays

try:
    from .heuristics import heuristic, is_deadlock
except ImportError:
    from heuristics import heuristic, is_deadlock


def reachable(board, player, crates):
    parent = {player: None}
    queue = deque([player])
    while queue:
        cur = queue.popleft()
        for move, (dr, dc) in DIRECTIONS:
            nxt = (cur[0] + dr, cur[1] + dc)
            if nxt in parent or nxt in crates or not board.is_floor(nxt):
                continue
            parent[nxt] = (cur, move)
            queue.append(nxt)
    return parent


def walk_path(parent, cell):
    moves = []
    while parent[cell] is not None:
        cell, move = parent[cell]
        moves.append(move)
    return ''.join(reversed(moves))


def push_successors(board, crates, parent):
    for crate in crates:
        for move, (dr, dc) in DIRECTIONS:
            stand = (crate[0] - dr, crate[1] - dc)   # cell the player must push from
            if stand not in parent:                  # can't get behind this crate
                continue
            transition = board.move(State(stand, crates), move)
            if transition is None or not transition.pushed:
                continue
            new_state = transition.state
            yield new_state.player, new_state.crates, walk_path(parent, stand) + move


def astar(board, start, time_limit=14.0, weight=1.0, count_pushes=False):
    deadline = time.time() + time_limit
    tie = count()

    if board.is_solved(start):
        return ''

    nodes = [(-1, '')]
    h0 = heuristic(board, start.crates)
    open_heap = [(weight * h0, h0, next(tie), 0, 0, start.player, start.crates)]
    closed = set()

    while open_heap:
        if time.time() > deadline:
            return None
        f, h, _, g, idx, player, crates = heapq.heappop(open_heap)

        parent = reachable(board, player, crates)
        key = (min(parent), crates)          # normalized player position
        if key in closed:
            continue
        closed.add(key)

        if board.is_solved(State(player, crates)):
            parts = []
            while idx != -1:
                parts.append(nodes[idx][1])
                idx = nodes[idx][0]
            return ''.join(reversed(parts))

        for new_player, new_crates, moves in push_successors(board, crates, parent):
            if is_deadlock(board, new_crates):
                continue
            nodes.append((idx, moves))
            step_cost = 1 if count_pushes else len(moves)
            new_g = g + step_cost
            new_h = heuristic(board, new_crates)
            heapq.heappush(open_heap, (new_g + weight * new_h, new_h, next(tie),
                                       new_g, len(nodes) - 1, new_player, new_crates))
    return None


def solve(width, height, mapData, itemsData):
    board, start = from_arrays(width, height, mapData, itemsData)
    result = astar(board, start, time_limit=8.0, weight=2.0, count_pushes=True)
    if result is not None:
        return result
    result = astar(board, start, time_limit=6.0, weight=3.0, count_pushes=False)
    return result if result is not None else ''