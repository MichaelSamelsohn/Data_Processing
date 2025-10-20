# Imports #
from Monopoly.Source.Bots.dummy import Dummy
from Monopoly.Source.game import Game
from Monopoly.Source.player import Human

if __name__ == "__main__":
    game = Game([Human(name="Michael"), Dummy("Bob")])
    for _ in range(10):
        game.play_turn()

