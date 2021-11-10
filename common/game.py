# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 11:44:56 2021

@author: Boss
"""
import random
from random import shuffle

nofw = 4
# import player as pl
# defining game dice
dice = ['2', '3', '4', '5', 'Your Choice', 'Your Choice']
# will store values of user
myTiles = []


# df representing bag with tiles and their values and amounts

class Game:
    def __init__(self, id, game_tiles):
        self.id = id
        self.clients: Player = {}
        self.ready = False
        self.bag = Bag(game_tiles)
        self.turn = 0
        self.currentPlayer = 0
        self.leader = 0
        self.rolled = False
        self.message = ""

    def setReady(self, leaderIndex):
        self.leader = leaderIndex
        self.ready = True

    def getGameBag(self):
        return self.bag

    def getCurrentPlayer(self):
        return self.currentPlayer

    def isReady(self):
        return self.ready

    def setClients(self, clients):
        self.clients = clients

    def setServerMessage(self, message):
        self.message = message

    def getServerMessage(self):
        return self.message

    def getPlayer(self, playerIndex):
        return self.clients[playerIndex]

    def setPlayer(self, playerIndex):
        self.currentPlayer = playerIndex

    def checkReady(self):
        toCheck = self.getPlayers()
        notReady = []
        for player in toCheck:
            if player.played is True:
                continue
            else:
                notReady.append(player.get_name())
        return notReady

    def resetPlayed(self):
        for player in self.clients:
            self.clients[player].played = False
        self.rolled = False

    def getPlayers(self):
        playersList = [self.clients[client] for client in self.clients]
        return playersList

    def setRacks(self, diceValue):
        for player in self.getPlayers():
            player.rack.add_to_rack(diceValue, self.bag)

    def setRolled(self):
        self.rolled = True

    def nextTurn(self):

        n = len(self.clients)
        if self.currentPlayer == n - 1:
            self.currentPlayer = 0
        else:
            self.currentPlayer += 1
        self.turn += 1
        self.rolled = False
        self.resetPlayed()


class Player:
    """
    
    Creates an instance of a player.
    Initializes the player's rack, and allows you
    to set/get a player name """

    def __init__(self, nofw, num, bag):
        # Intializes a player instance. Creates the player's rack by creating an instance of that class.
        # Takes the bag as an argument, in order to create the rack.
        self.name = ""
        self.rack = Rack(nofw, bag)
        self.money = 200
        self.number = num
        self.sell_check = True
        self.wordvalue = 0
        self.message = ""
        self.played = False
        self.start = False
        self.score = 0

    def set_name(self, name):
        # Sets the player's name.
        self.name = name

    def set_start(self):
        # Sets the player's name.
        self.start = True

    def get_name(self):
        # Gets the player's name.
        return self.name

    def setPlayerMessage(self, message):
        self.message = message

    def addPlayerMessage(self, message):
        self.message += message

    def get_rack_str(self):
        # Returns the player's rack.
        return self.rack.get_rack_str()

    def get_temp_str(self):
        # Returns the player's rack.
        return self.rack.get_temp_str()

    def get_rack_arr(self):
        # Returns the player's rack in the form of an array.
        return self.rack.get_rack_arr()

    def get_rack_list(self):
        return self.rack.get_rack_list()

    def increase_money(self, increase):
        # Increases the player's score by a certain amount. Takes the increase (int) as an argument and adds it to the score.
        self.money += increase

    def get_money(self):
        # Returns the player's score
        return self.money

    def buy_word(self):
        self.money -= self.rack.get_temp_value()
        self.rack.add_to_main()
        return self

    def word_check(self, word):
        word = word.upper()
        racklist = self.get_rack_list()
        wildnumb = 0
        for w in word:
            if w not in racklist:
                if 'WILD' not in racklist:
                    return (False)
                    break
                elif wildnumb > 0:
                    return (False)
                    break
                else:
                    racklist.remove('WILD')
                    wildnumb += 1
            else:
                racklist.remove(w)
        return (True)

    def word_value(self):
        score = 0
        for tile in self.sellword:
            score += tile.score
        return (score ** 2)

    def word_remove(self, word):
        word = word.upper()
        for w in word:
            for tile in self.get_rack_arr():
                if tile.letter == w:
                    self.rack.remove_from_rack(tile)
                    break
        return (self)

    def sell_word(self, word):
        word = word.upper()
        self.sellword = []
        for w in word:
            if w in self.get_rack_list():
                for tile in self.get_rack_arr():
                    if w == tile.letter:
                        self.sellword.append(tile)
                        self.rack.remove_from_rack(tile)
                        break
            else:
                for tile in self.get_rack_arr():
                    if 'WILD' == tile.letter:
                        self.sellword.append(tile)
                        self.rack.remove_from_rack(tile)
                        break
        return (self)

    def sell(self, word):
        if word.lower() in WordDict:
            self.sell_check = self.word_check(word)
            if self.sell_check:
                self.sell_word(word)
                self.wordvalue = int(self.word_value())
                self.money += self.wordvalue
        else:
            self.sell_check = False
        return (self)


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

    def add_wild_to_rack(self, nofw, bag):

        for i in range(nofw):
            self.rack.append(bag.take_wild_bag())

    def add_to_main(self):
        self.rack += self.temp
        self.temp = []

    # def initialize(self):
    #     # Adds the initial tiles to the player's hand.
    #     self.temp = []
    #     for i in range(self.diceValue):
    #         self.add_to_rack()

    def get_rack_str(self):
        # Displays the user's rack in string form.
        return ", ".join(str(item.get_letter()) for item in self.rack)

    def get_rack_list(self):
        return [str(item.get_letter()) for item in self.rack]

    def get_rack_arr(self):
        # Returns the rack as an array of tile instances
        return self.rack

    def get_temp_str(self):
        # Displays the user's rack in string form.
        return ", ".join(str(item.get_letter()) for item in self.temp)

    def get_temp_arr(self):
        # Returns the rack as an array of tile instances
        return self.temp

    def remove_from_rack(self, tile):
        # Removes a tile from the rack (for example, when a tile is being played).
        self.rack.remove(tile)

    def clear_rack(self):

        self.temp = []

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
        self.initialize_bag(game_tiles)

    def add_to_bag(self, tile, quantity):
        # Adds a certain quantity of a certain tile to the bag.
        # Takes a tile and an integer quantity as arguments.
        for i in range(quantity):
            self.bag.append(tile)

    def initialize_bag(self, game_tiles):
        # Adds the intiial 108 tiles to the bag.
        for index, row in game_tiles.iterrows():
            # print(index, row['NO'], row['VALUE'])
            self.add_to_bag(Tile(index, game_tiles.loc[:, "VALUE"], game_tiles), row['NO'])

        shuffle(self.bag)

    def take_from_bag(self):
        # Removes a tile from the bag and returns it to the user.
        # This is used for replenishing the rack.
        return self.bag.pop()

    def get_remaining_tiles(self):
        # Returns the number of tiles left in the bag.
        return len(self.bag)

    def take_wild_bag(self):
        for i in range(len(self.bag)):
            if self.bag[i].letter == 'WILD':
                return self.bag.pop(i)


class Tile:
    """
    Class that allows for the creation of a tile.
    Initializes using an uppercase string of one letter,
    and an integer representing that letter's score.
    """

    def __init__(self, letter, letter_values, game_tiles):
        # Initializes the tile class. Takes the letter as a string,
        # and the dictionary of letter values as arguments.
        self.letter = letter.upper()
        if self.letter in game_tiles.loc[:, "VALUE"]:
            self.score = game_tiles.loc[self.letter, 'VALUE']
        else:
            self.score = 0

    def get_letter(self):
        # Returns the tile's letter (string).
        return self.letter

    def get_score(self):
        # Returns the tile's score value.
        return self.score


# function to simulate rolling dice
def dice_roll():
    choice = random.choice(dice)
    print("rolling dice...", choice)
    # print(choice)
    if choice == 'Your Choice':
        while choice not in [2, 3, 4, 5]:
            choice = int(input("Enter a number from 2-5:  "))
            if choice not in [2, 3, 4, 5]:
                print("invalid input. Please enter number from 2-5")
        # print(choice)
    print("")
    return choice
