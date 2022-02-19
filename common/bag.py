from random import shuffle

from common.gameconstants import WILD_CARD
from common.tile import Tile


class Bag:
    """
    Creates the bag of all tiles that will be available during the game.
    Contains 108 letters and nine wild tiles.
    Takes no arguments to initialize.
    """

    def __init__(self, game_tiles):
        # Creates the bag full of game tiles,
        # and calls the initialize_bag() method,
        # which adds the default 100 tiles to the bag.
        # Takes no arguments.
        self.bag = []
        self.wildcard_bag = []
        self.tile_id = 0
        self.initialize_bag(game_tiles)

    def add_to_bag(self, tile: Tile, quantity):
        # Adds a certain quantity of a certain tile to the bag.
        # Takes a tile and an integer quantity as arguments.
        for i in range(quantity):
            copy_t = tile.__copy__()
            self.tile_id += 1
            copy_t.set_tile_id(self.tile_id)
            if copy_t.letter == WILD_CARD:
                self.wildcard_bag.append(copy_t)
            else:
                self.bag.append(copy_t)

    def initialize_bag(self, game_tiles):
        # Adds the intiial 108 tiles to the bag.
        for index, row in game_tiles.iterrows():
            # print(index, row['NO'], row['VALUE'])
            self.tile_id += 1
            self.add_to_bag(Tile(self.tile_id, index, game_tiles), row['NO'])

        shuffle(self.bag)

    def take_from_bag(self):
        # Removes a tile from the bag and returns it to the user.
        # This is used for replenishing the rack.
        return self.bag.pop()

    def return_to_bag(self, tile):
        if tile.letter == WILD_CARD:
            self.wildcard_bag.append(tile)
        else:
            self.bag.append(tile)

    def get_remaining_tiles(self):
        # Returns the number of tiles left in the bag.
        return len(self.bag)

    def take_wild_bag(self):
        return self.wildcard_bag.pop()