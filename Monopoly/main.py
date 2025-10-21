# Imports #
import time

from Monopoly.Source.Bots.easy import Easy
from Monopoly.Source.Bots.dummy import Dummy
from Monopoly.Source.Bots.easy import Easy
from Monopoly.Source.game import Game

if __name__ == "__main__":
    game = Game([Easy(name="Alice"), Dummy(name="Bob")])
    for _ in range(100):
        game.play_turn()
        time.sleep(1)

