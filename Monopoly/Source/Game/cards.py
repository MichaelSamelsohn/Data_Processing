import random

from Monopoly.Settings.monopoly_settings import *
from Monopoly.Source.Game.board import RealEstate


class Card:
    def __init__(self, description, effect):
        self.description = description
        self.effect = effect

    def apply(self, player, game):
        log.info(self.description)
        self.effect(player, game)


class Deck:
    def __init__(self, cards):
        self.cards = cards[:]  # TODO: Is this slicing necessary?
        log.info("Shuffling deck cards")
        random.shuffle(self.cards)

    def draw(self):
        card = self.cards.pop(0)
        self.cards.append(card)
        return card


def advance_to_go(player, game):
    player.position = 0
    player.cash += GO_SALARY


def advance_to_illinois_avenue(player, game):
    # Illinois avenue is at position 24.
    game.move_player(player=player, steps={7: 17, 22: 2, 36: 28}.get(player.position))
    game.handle_space(player=player, dice_roll=0)


def advance_to_st_charles_place(player, game):
    # St. Charles place is at position 11.
    game.move_player(player=player, steps={7: 4, 22: 29, 36: 15}.get(player.position))
    game.handle_space(player=player, dice_roll=0)


def advance_to_nearest_utility(player, game):
    # Electric company is at position 12.
    # Water works is at position 28.
    game.move_player(player=player, steps={7: 5, 22: 6, 36: 16}.get(player.position))
    game.handle_space(player=player, dice_roll=None)


def advance_to_nearest_railroad(player, game):
    # Pennsylvania Railroad at position 15 is nearest to chance position 7.
    # B&O Railroad at position 25 is nearest to chance position 22.
    # Reading Railroad at position 5 is nearest to chance position 36.
    game.move_player(player=player, steps={7: 8, 22: 3, 36: 9}.get(player.position))
    game.handle_space(player=player, dice_roll=None)


def bank_pays_dividend(player, game):
    player.cash += 50


def get_free_card(player, game):
    player.free_cards += 1


def go_back_3_spaces(player, game):
    player.position -= 3


def go_to_jail(player, game):
    player.in_jail = True
    player. position = 10
    player.post_roll = True  # Player has rolled the dice for this turn and landed in jail through a chance card.
    player.consecutive_double_rolls = 0  # Reset the counter.


def general_repairs(player, game):
    repairs_cost = 0
    for space in player.spaces:
        if isinstance(space, RealEstate):
            repairs_cost += space.houses * 25 + (100 if space.hotel else 0)

    player.cash -= repairs_cost


def pay_poor_tax(player, game):
    player.cash -= 15


def advance_to_reading_railroad(player, game):
    # Reading Railroad at position 5 is nearest to chance position 36.
    game.move_player(player=player, steps={7: 38, 22: 23, 36: 9}.get(player.position))
    game.handle_space(player=player, dice_roll=None)
    # TODO: Rent should be standard rate not double as the 'advance_to_nearest_railroad' card.


def advance_to_boardwalk(player, game):
    # Boardwalk is at position 39.
    game.move_player(player=player, steps={7: 32, 22: 17, 36: 3}.get(player.position))
    game.handle_space(player=player, dice_roll=0)


def board_chairman(player, game):
    other_players = [p for p in game.players if p != player]
    for other_player in other_players:
        player.cash -= 50
        other_player.cash += 50


def building_loan_matures(player, game):
    player.cash += 150


def crossword_competition(player, game):
    player.cash += 100


def create_chance_deck():
    log.info("Generating the chance deck")
    return Deck([
        Card(description="Advance to GO", effect=advance_to_go),
        Card(description="Advance to Illinois Avenue", effect=advance_to_illinois_avenue),
        Card(description="Advance to St. Charles Place", effect=advance_to_st_charles_place),
        Card(description="Advance to the nearest Utility", effect=advance_to_nearest_utility),
        Card(description="Advance to the nearest Railroad", effect=advance_to_nearest_railroad),
        Card(description="Bank pays you dividend of 50$", effect=bank_pays_dividend),
        Card(description="Get out of Jail Free", effect=get_free_card),
        Card(description="Go Back Three 3 Spaces", effect=go_back_3_spaces),
        Card(description="Go to Jail. Go directly to Jail. Do not pass GO, do not collect 200$", effect=go_to_jail),
        Card(description="Make general repairs on all your property: For each house pay 25$, For each hotel pay 100$",
             effect=general_repairs),
        Card(description="Pay poor tax of 15$", effect=pay_poor_tax),
        Card(description="Take a trip to Reading Railroad", effect=advance_to_reading_railroad),
        Card(description="Advance to Boardwalk", effect=advance_to_boardwalk),
        Card(description="You have been elected Chairman of the Board. Pay each player 50$", effect=board_chairman),
        Card(description="Your building and loan matures. Collect 150$", effect=building_loan_matures),
        Card(description="You have won 100$ in a crossword competition", effect=crossword_competition)
    ])


def bank_error(player, game):
    player.cash += 200


def doctor_fees(player, game):
    player.cash -= 50


def grand_opera_night(player, game):
    other_players = [p for p in game.players if p != player]
    for other_player in other_players:
        player.cash += 50
        other_player.cash -= 50


def holiday_fund_matures(player, game):
    player.cash += 100


def income_tax_refund(player, game):
    player.cash += 20


def birthday_present(player, game):
    other_players = [p for p in game.players if p != player]
    for other_player in other_players:
        player.cash += 10
        other_player.cash -= 10


def life_insurance_matures(player, game):
    player.cash += 100


def hospital_fees(player, game):
    player.cash -= 100


def school_fees(player, game):
    player.cash -= 150


def consultancy_fee(player, game):
    player.cash -= 25


def street_repairs(player, game):
    repairs_cost = 0
    for space in player.spaces:
        if isinstance(space, RealEstate):
            repairs_cost += space.houses * 40 + (115 if space.hotel else 0)

    player.cash -= repairs_cost


def beauty_contest(player, game):
    player.cash += 10


def create_community_chest_deck():
    log.info("Generating the community chest deck")
    return Deck([
        Card(description="Advance to GO", effect=advance_to_go),
        Card(description="Bank error in your favor. Collect 200$", effect=bank_error),
        Card(description="Doctor's fees. Pay 50$", effect=doctor_fees),
        Card(description="Get out of jail free", effect=get_free_card),
        Card(description="Go to Jail. Go directly to Jail. Do not pass GO, do not collect 200$", effect=go_to_jail),
        Card(description="Grand opera night. Collect 50$ from every player for opening night seats",
             effect=grand_opera_night),
        Card(description="Holiday fund matures. Receive 100$", effect=holiday_fund_matures),
        Card(description="Income tax refund. Collect 20$", effect=income_tax_refund),
        Card(description="It is your birthday. Collect 10$ from every player", effect=birthday_present),
        Card(description="Life insurance matures – Collect 100$", effect=life_insurance_matures),
        Card(description="Hospital fees. Pay 100$", effect=hospital_fees),
        Card(description="School fees. Pay 150$", effect=school_fees),
        Card(description="Receive 25$ consultancy fee", effect=consultancy_fee),
        Card(description="You are assessed for street repairs – 40$ per house, 115$ per hotel", effect=street_repairs),
        Card(description="You have won second prize in a beauty contest. Collect 10$", effect=beauty_contest)
    ])
