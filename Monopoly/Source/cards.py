import random

from Monopoly.Settings.monopoly_settings import *


class Card:
    def __init__(self, description, effect):
        self.description = description
        self.effect = effect

    def apply(self, player, game):
        log.debug(f"Card: {self.description}")
        self.effect(player, game)


class Deck:
    def __init__(self, cards):
        self.cards = cards[:]  # TODO: Is this slicing necessary?
        log.debug("Shuffling deck cards")
        random.shuffle(self.cards)

    def draw(self):
        card = self.cards.pop(0)
        self.cards.append(card)
        return card


def advance_to_go(player, game):
    player.position = 0
    player.cash += GO_SALARY
    print(f"{player.name} advances to GO and collects $200")


def go_to_jail(player, game):
    player.position = game.jail_position
    player.in_jail = True
    print(f"{player.name} goes directly to jail!")


def get_out_of_jail_free(player, game):
    player.free_cards += 1
    log.debug(f"{player.name} got a 'get out of jail free' card")


def earn_50(player, game):
    player.cash += 50
    print(f"{player.name} receives $50")


def pay_50(player, game):
    player.cash -= 50
    print(f"{player.name} pays $50")


def move_back_3(player, game):
    player.position = (player.position - 3) % 40
    print(f"{player.name} moves back 3 spaces")
    game.handle_space(player)


def create_chance_deck():
    log.info("Generating the chance deck")
    return Deck([
        Card("Advance to GO", advance_to_go),
        Card("Go to Jail", go_to_jail),
        Card("Bank pays you dividend of $50", earn_50),
        Card("Pay poor tax of $50", pay_50),
        Card("Go back 3 spaces", move_back_3)
    ])


def create_community_chest_deck():
    log.info("Generating the community chest deck")
    return Deck([
        Card("Advance to GO", advance_to_go),
        Card("Doctor's fees – Pay $50", pay_50),
        Card("From sale of stock you get $50", earn_50),
        Card("Go to Jail", go_to_jail)
    ])


"""
(Listed from a commonly used “classic” edition) 
Advance to GO (Collect $200)
Advance to Illinois Avenue — If you pass GO, collect $200
Advance to St. Charles Place — If you pass GO, collect $200
Advance token to nearest Utility — If unowned, you may buy it; if owned, throw dice and pay owner 10× the amount shown
Advance token to the nearest Railroad; pay owner twice the rental to which he/she is otherwise entitled; if railroad is unowned, you may buy it
Bank pays you dividend of $50
Get Out of Jail Free
Go Back 3 Spaces
Go to Jail — Go directly to jail — Do not pass GO — Do not collect $200
Make general repairs on all your property — For each house pay $25, for each hotel pay $100
Pay poor tax of $15
Take a trip to Reading Railroad — If you pass GO, collect $200
Take a walk on the Boardwalk — Advance token to Boardwalk
You have been elected Chairman of the Board — Pay each player $50
Your building and loan matures — Collect $150
You have won a crossword competition — Collect $100
"""

"""
Advance to GO (Collect $200)
Bank error in your favor — Collect $200
Doctor’s fee — Pay $50
From sale of stock you get $50
Get Out of Jail Free
Go to Jail — Go directly to jail — Do not pass GO — Do not collect $200
Grand Opera Night — Collect $50 from every player for opening night seats
Holiday Fund matures — Receive $100
Income tax refund — Collect $20
It is your birthday — Collect $10 from every player
Life insurance matures — Collect $100
Pay hospital fees of $100
Pay school fees of $150
Receive $25 consultancy fee
You are assessed for street repairs — $40 per house, $115 per hotel
You have won second prize in a beauty contest — Collect $10
You inherit $100
"""
