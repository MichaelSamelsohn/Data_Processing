# Imports #
from Monopoly.Settings.monopoly_settings import log
from Monopoly.Source.Game.game import Game
from Monopoly.Source.Game.player import Human
from Monopoly.Source.Bots.dummy import Dummy
from Monopoly.Source.Bots.easy import Easy

if __name__ == "__main__":
    game = Game([Easy(name="Alice"), Easy(name="Bob")])
    for turn in range(500):
        log.info("")
        log.info(f"--- Turn #{turn + 1} ---")
        log.info("")

        game.play_turn()
        # time.sleep(1)

