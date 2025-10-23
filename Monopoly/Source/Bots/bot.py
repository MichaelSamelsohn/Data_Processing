# Imports #
from abc import abstractmethod

from Monopoly.Source.player import Player


class Bot(Player):
    def __init__(self, name, role):
        super().__init__(name=name, role=role)

    @abstractmethod
    def play_turn_logic(self, board, players):
        pass

    @abstractmethod
    def buy_space_logic(self, space):
        pass

    @abstractmethod
    def auction_logic(self, space, latest_bid):
        pass

    @abstractmethod
    def raise_cash_logic(self):
        pass

    @abstractmethod
    def trade_acceptance_logic(self, trade_offer_initiator,
                               initiator_space_offer, initiator_cash_offer, initiator_free_cards_offer,
                               recipient_space_offer, recipient_cash_offer, recipient_free_cards_offer):
        pass

    @abstractmethod
    def development_logic(self):
        pass

    @abstractmethod
    def monopoly_build_selection_logic(self):
        pass

    @abstractmethod
    def space_build_selection_logic(self):
        pass

    @abstractmethod
    def monopoly_sell_selection_logic(self):
        pass

    @abstractmethod
    def space_sell_selection_logic(self):
        pass

    @abstractmethod
    def management_logic(self):
        pass

    @abstractmethod
    def mortgage_logic(self):
        pass

    @abstractmethod
    def redeem_logic(self):
        pass