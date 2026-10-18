import time

try:
    from .search import solve
except ImportError:
    from search import solve

class SokoBot:
    def solveSokobanPuzzle(self, width, height, mapData, itemsData):
        # YOU NEED TO REWRITE THE IMPLEMENTATION OF THIS METHOD TO MAKE THE BOT SMARTER
        # Default stupid behavior: Think (sleep) for 3 seconds, and then return a
        # sequence
        # that just moves left and right repeatedly.
        try:
            return solve(width, height, mapData, itemsData)
        except Exception as ex:
            print(ex)
            return ""
