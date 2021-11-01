# -*- coding: utf-8 -*-
"""
Created on Fri Mar 26 14:08:18 2021

@author: Boss
"""
import sys
import time

from common import *

nofw = 4
status = ""

user_ans = ""


def receivedRacks(myPlayer, n, myNumber):
    name = "Name: "
    Dice = "Dice: "
    Bought = "buying racks "
    Sold = "Sold: "
    get = "get"
    Iplayed = "Played"
    print("Your rack contains: ")
    for tile in myPlayer.get_rack_arr():
        print(tile.letter, tile.score)

    print("New letters: ")
    for tile in myPlayer.rack.get_temp_arr():
        print(tile.letter, tile.score)
    print("Total value of your draw is: ", myPlayer.rack.get_temp_value())
    # %% buying
    if myPlayer.money >= myPlayer.rack.get_temp_value():
        print("You have:  $", myPlayer.money)
        user_ans = ""
        while user_ans.upper() != ("Y" or "N"):
            user_ans = input("Do you want to buy words? (Y-N)").upper()
            time.sleep(1)
            print(f" you entered {user_ans}")
            if user_ans == "Y":
                print("user wants to buy")
                try:
                    myGame = n.send(Bought)
                except Exception as e:
                    print(e)
                while True:
                    serverMessage = myGame.getServerMessage()
                    print(f"serverMessage: {serverMessage} ")
                    if "Purchased" in serverMessage:
                        break
                    else:
                        try:
                            myGame = n.send(get)
                        except Exception as e:
                            continue
                myPlayer = myGame.getPlayer(myNumber)
                print("you now have $", myPlayer.money)
            else:
                break
    else:
        print("You have insufficient funds to purchase tiles")
    # %% selling
    print("Your rack contains: ")
    for tile in myPlayer.get_rack_arr():
        print(tile.letter, tile.score)
    sell = input("Do you want to sell any words? Y/N ")
    if sell.upper() == "Y":
        attempt = 3
        while attempt > 0:
            wordToSell = input("input word to sell: ")

            myPlayer.sell(wordToSell)

            if myPlayer.sell_check:
                Sold += wordToSell
                myGame = n.send(Sold)
                time.sleep(1)
                # myGame = n.send(Sold)
                # time.sleep(1)
                while True:
                    myGame = n.send(get)
                    time.sleep(1)
                    serverMessage = myGame.getServerMessage()
                    print(f"serverMessage: {serverMessage} ")
                    if "SOLD" in serverMessage:
                        break
                myPlayer = myGame.getPlayer(myNumber)

                print("You sold by $", myPlayer.wordvalue)
                # myPlayer.addPlayerMessage(f" sold {wordToSell}")
                break
            else:
                attempt -= 1
                print(
                    f"You failed to sell the word,{attempt} attempts left"
                )
        print("You now have: $", myPlayer.money)
        # %% done selling
        # sending player object to game
    myGame = n.send(Iplayed)
    return myGame
    # %%


def main():
    name = "Name: "
    Dice = "Dice: "
    Bought = "buying racks "
    Sold = "Sold: "
    get = "get"
    firstRun = True
    i = 0
    print("lets send network")
    try:
        n = network.Network()
        print("we connected to network")
        print(n.p)
        myNumber = n.p
    except Exception as e:
        print(e)
        print("couldnt connect")
        sys.exit("Cant connect to host")

    run = True
    # firstRun = True
    inLobby = True
    print(f" I am player number {myNumber}")
    # %%
    nameEntered = False
    iReady = False
    while run:
        if firstRun:
            print("welcome to buyGame")
            firstRun = False
        else:
            print(f"round {i}")
        # if firstRun:
        try:
            myGame = n.send("get")
        except Exception as e:
            # run = False
            print("cant get game")
            print(e)
            break
            # firstRun = False

        # backupGame = myGame
        user_ans = ""

        if myGame is not False:
            myPlayer = myGame.getPlayer(myNumber)
            # print("number success")
        # %%  lobby

        while inLobby:
            myGame = n.send("get")
            if not nameEntered:
                myName = "Name: " + str(input("enter your name: "))

                try:
                    myGame = n.send(myName)
                    nameEntered = True
                except Exception as e:
                    print(e)
                time.sleep(1)
            if not iReady:
                user_ans = input("enter 'ready' to begin game: ").upper()
                if "READY" in user_ans:
                    try:
                        iReady = True
                        myGame = n.send("start")
                        time.sleep(1)
                    except Exception as e:
                        print(e)

            if myGame.ready:
                # %% all connected players are ready
                print("game state is ready ")
                print(f"{len(myGame.getPlayers())} players are connnected")
                beginOrNo = input("Do you want to begin (Y/N) ").upper()
                print(myGame.getServerMessage())
                if beginOrNo == 'Y':
                    inLobby = False
                    if myGame.leader == myNumber:
                        print("You are the leader you begin")
            # %% some connected players are not ready
            else:
                print("waiting for other player")

        # %% # outside lobby now it is the game

        # check if we rolled dice yet
        # %%
        if myGame.rolled is True:
            # leader rolled
            serverMessage = myGame.getServerMessage()

            # %% racks are handed
            if "Racks" in serverMessage:
                try:
                    myPlayer = myGame.getPlayer(myNumber)
                    myGame = receivedRacks(myPlayer, n, myNumber)
                    myGame = n.send("Done")
                except Exception as e:
                    print(e)
            # players could be done
            # %%
            if "Done" in myGame.getServerMessage():
                print(f"round {i} done, time for next round ")
                i += 1
            elif "not ready" in myGame.getServerMessage():
                print(myGame.getServerMessage())
        # %%
        else:
            # we have not rolled dice

            if myNumber == myGame.currentPlayer:
                # it is my turn to roll
                print("it is your turn to roll")
                input("Press enter to roll dice:")
                diceValue = str(game.dice_roll())
                diceMessage = Dice + diceValue
                try:
                    myGame = n.send(diceMessage)
                except Exception as e:
                    print(e)
            # %% some one else is playing
            else:
                # it is someone elses turn to roll
                i = myGame.turn
                print(f"Player {myGame.currentPlayer} needs to roll")

        # %% done rolling


# %%


if __name__ == '__main__':
    main()
