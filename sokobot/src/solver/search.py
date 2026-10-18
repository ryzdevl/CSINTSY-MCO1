import heapq
import time
from collections import deque
from itertools import count
from functools import lru_cache

try:
    from .game_logic import DIRECTIONS, State, from_arrays
except ImportError:
    from game_logic import DIRECTIONS, State, from_arrays

@lru_cache(maxsize=64)
def target_distances(board):

    distances = []

    for target in sorted(board.targets):
        distance = {target: 0}
        queue = deque([target])

        while queue:
            current = queue.popleft()

            for move, (dr, dc) in DIRECTIONS:
                previous = (current[0] - dr, current[1] - dc)
                player_pos = (previous[0] - dr, previous[1] - dc)

                if (previous not in distance and board.is_floor(previous) 
                    and board.is_floor(player_pos)):

                    distance[previous] = distance[current] + 1
                    queue.append(previous)

        distances.append(distance)

    return tuple(distances)

@lru_cache(maxsize=50000)
def heuristic(board, crates):
    if crates == board.targets:
        return 0

    crates_list = sorted(crates)
    distances = target_distances(board)
    n = len(crates_list)

    if n != len(distances):
        return float('inf')

    dp = {0: 0}

    for crate in crates_list:
        next_dp = {}

        for mask, cost in dp.items():
            for i, distance_map in enumerate(distances):
                bit = 1 << i

                if mask & bit:
                    continue

                push_distance = distance_map.get(crate)

                if push_distance is None:
                    continue

                new_mask = mask | bit
                new_cost = cost + push_distance

                if new_cost < next_dp.get(new_mask, float('inf')):
                    next_dp[new_mask] = new_cost

        if not next_dp:
            return float('inf')

        dp = next_dp

    return dp.get((1 << n) - 1, float('inf'))

@lru_cache(maxsize=50000)
def is_deadlock(board, crates):

    if crates == board.targets:
        return False

    distances = target_distances(board)
    reachable_squares = set()

    for distance_map in distances:
        reachable_squares.update(distance_map.keys())

    for crate in crates:
        if crate not in board.targets and crate not in reachable_squares:
            return True

    blocked = board.walls | crates

    for r, c in crates:
        if(r, c) in board.targets:
            continue

        for dr in (-1, 0):
            for dc in (-1, 0):
                square = {(r + dr, c + dc), (r + dr + 1, c + dc), 
                          (r + dr, c + dc + 1), (r + dr + 1, c + dc + 1)}

                if square.issubset(blocked):
                    return True

    if heuristic(board, crates) == float('inf'):
        return True

    return False

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


def astar(board, start, time_limit=14.0, weight=1.0):
    deadline = time.time() + time_limit
    tie = count()

    if board.is_solved(start):
        return ''

    # nodes[i] = (parent_index, move_string); used only to rebuild the answer
    nodes = [(-1, '')]
    h0 = heuristic(board, start.crates)
    # heap item: (f, h, tie, g, node_index, player, crates)
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
            new_g = g + len(moves)           # cost = total moves (walk + push)
            new_h = heuristic(board, new_crates)
            heapq.heappush(open_heap, (new_g + weight * new_h, new_h, next(tie),
                                       new_g, len(nodes) - 1, new_player, new_crates))
    return None


def solve(width, height, mapData, itemsData):
    board, start = from_arrays(width, height, mapData, itemsData)
    result = astar(board, start)
    return result if result is not None else ''