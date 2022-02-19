class Tile:
    """
    Class that allows for the creation of a tile.
    Initializes using an uppercase string of one letter,
    and an integer representing that letter's score.
    """

    def __init__(self, tile_id, letter, game_tiles):
        # Initializes the tile class. Takes the letter as a string,
        # and the dictionary of letter values as arguments.
        self.t_id = tile_id
        self.letter = letter.upper()
        self.game_tiles = game_tiles
        if self.letter in game_tiles.loc[:, "VALUE"]:
            self.score = game_tiles.loc[self.letter, 'VALUE']
        else:
            self.score = 0

    def __repr__(self):
        return f"{self.t_id}-{self.letter}"

    def __copy__(self):
        return Tile(-1, self.letter, self.game_tiles)

    def set_tile_id(self, _id: int):
        self.t_id = _id

    def get_tile_id(self):
        return self.t_id

    def get_letter(self):
        # Returns the tile's letter (string).
        return self.letter

    def get_score(self):
        # Returns the tile's score value.
        return self.score