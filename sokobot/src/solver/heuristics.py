from collections import deque
from functools import lru_cache

try:
    from .game_logic import DIRECTIONS
except ImportError:
    from game_logic import DIRECTIONS


@lru_cache(maxsize=64)
def _target_distances(board):

    distances = []
    for target in sorted(board.targets):
        distance = {target: 0}
        queue = deque([target])

        while queue:
            current = queue.popleft()
            for _, (dr, dc) in DIRECTIONS:
                previous = (current[0] - dr, current[1] - dc)
                player_stand = (previous[0] - dr, previous[1] - dc)
                if (previous not in distance
                        and board.is_floor(previous)
                        and board.is_floor(player_stand)):
                    distance[previous] = distance[current] + 1
                    queue.append(previous)

        distances.append(distance)
    return tuple(distances)


@lru_cache(maxsize=50000)
def heuristic(board, crates):
    if crates == board.targets:
        return 0

    crate_positions = sorted(crates)
    distance_maps = _target_distances(board)
    n = len(crate_positions)
    if n != len(distance_maps):
        return float('inf')

    dp = {0: 0}
    for crate in crate_positions:
        next_dp = {}
        for mask, cost in dp.items():
            for target_index, distances in enumerate(distance_maps):
                bit = 1 << target_index
                if mask & bit:
                    continue 
                push_distance = distances.get(crate)
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

    distances = _target_distances(board)
    can_reach_a_target = set().union(*(set(d) for d in distances))
    if any(crate not in board.targets and crate not in can_reach_a_target
           for crate in crates):
        return True

    blocked = board.walls | crates
    for r, c in crates:
        if (r, c) in board.targets:
            continue
        for dr in (-1, 0):
            for dc in (-1, 0):
                square = {(r + dr, c + dc), (r + dr + 1, c + dc),
                          (r + dr, c + dc + 1), (r + dr + 1, c + dc + 1)}
                if square <= blocked:
                    return True

    return heuristic(board, crates) == float('inf')
