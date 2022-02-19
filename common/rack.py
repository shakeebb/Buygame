from common.gameconstants import WILD_CARD


class Rack:
    """
    Creates each player's 'dock', or 'hand'. Allows players to add, remove and replenish the number of tiles in their hand.
    """

    def __init__(self, nofw, bag):
        # Initializes the player's rack/hand. Takes the bag from which the racks tiles will come as an argument.
        self.rack = []
        self.temp = []
        # self.bag = bag
        # self.diceValue = diceValue
        self.add_wild_to_rack(nofw, bag)
        # self.initialize(diceValue)

        # self.get_temp_arr()
        # self.get_temp_value()

    # def setRack(self, bag, diceValue):
    #     self.bag = bag
    #     self.diceValue = diceValue

    def add_to_rack(self, diceValue, bag):
        # Takes a tile from the bag and adds it to the player's rack.
        for i in range(diceValue):
            self.temp.append(bag.take_from_bag())

    def rollback_rack(self, bag):
        value = self.get_temp_value()
        # for now stick to variation 1, whereby tiles are out of play
        # and doesn't returned to the bag
        self.get_temp_arr().clear()
        return value

    def add_wild_to_rack(self, nofw, bag):
        for i in range(nofw):
            self.rack.append(bag.take_wild_bag())

    def add_to_main(self):
        self.rack += self.temp
        buy_rack = self.temp
        self.temp = []
        return buy_rack

    # def initialize(self):
    #     # Adds the initial tiles to the player's hand.
    #     self.temp = []
    #     for i in range(self.diceValue):
    #         self.add_to_rack()

    def get_rack_str(self):
        # Displays the user's rack in string form.
        return ",".join(str(item.get_letter() if item is not None else "-") for item in self.rack)

    def get_rack_list(self):
        return [str(item.get_letter()) if item is not None else "" for item in self.rack]

    def get_rack_arr(self):
        # Returns the rack as an array of tile instances
        return self.rack

    def get_temp_str(self):
        # Displays the user's rack in string form.
        return ",".join(str(item.get_letter()) for item in self.temp)

    def get_temp_arr(self):
        # Returns the rack as an array of tile instances
        return self.temp

    def remove_from_rack(self, tile):
        # Removes a tile from the rack (for example, when a tile is being played).
        self.rack.remove(tile)

    def clear_temp_rack(self):
        cleared_rack = self.temp
        self.temp = []
        return cleared_rack

    def get_temp_value(self):
        score = 0
        for tile in self.get_temp_arr():
            score += tile.score
        score = score * score
        # self.rackValue = score
        return score

    def get_rack_length(self):
        # Returns the number of tiles left in the rack.
        return len(self.get_rack_list())

    def replenish_rack(self):
        # Adds tiles to the rack after a turn such that the rack will have 7 tiles (assuming a proper number of tiles in the bag).
        while self.get_rack_length() < 7 and self.bag.get_remaining_tiles() > 0:
            self.add_to_rack()

    def updateGameBag(self, bag):
        self.bag = bag

    def num_non_wildcard_letters(self):
        return len(list(filter(lambda item: item is not None and item.letter != WILD_CARD, self.rack)))