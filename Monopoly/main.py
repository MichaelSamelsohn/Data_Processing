from Monopoly.Source.game import Game
from Monopoly.Source.player import Dummy, Human

if __name__ == "__main__":
    game = Game([Human(name="Michael"), Dummy("BOT")])
    for _ in range(10):
        game.play_turn()

