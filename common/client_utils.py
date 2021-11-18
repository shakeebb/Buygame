import time

from common.game import Game, Player
from common.gameconstants import ClientMsg, GameStatus, Colors
from common.logger import log
from common.network import Network


def default_notification(msg: str, color: Colors = Colors.BLACK):
    print(str)


def process_rack(rack: [], temp=False):
    pass


class ClientUtils:

    @staticmethod
    def check_game_events(game: Game,
                          number: int,
                          network: Network,
                          notify_srv_msg: default_notification,
                          notify_cln_msg: default_notification):
        # check if we rolled dice yet
        if game.rolled is True:
            # leader rolled
            serverMessage = game.getServerMessage()
            notify_srv_msg(serverMessage)

            # %% racks are handed
            if "Racks" in serverMessage:
                return GameStatus.RECEIVE_RACKS

            # players could be done
            # %%
            if "Done" in game.getServerMessage():
                notify_cln_msg(f"round {i} done, time for next round ")
                # ?? i += 1
            elif "not ready" in game.getServerMessage():
                notify_srv_msg(game.getServerMessage())
        # %%
        else:
            # we have not rolled dice
            if number == game.currentPlayer:
                # it is my turn to roll
                notify_cln_msg("it is your turn to roll dice")
                return GameStatus.ROLL_DICE
            # %% some one else is playing
            else:
                # it is someone elses turn to roll
                i = game.turn
                notify_cln_msg(f"Player {game.currentPlayer} needs to roll")
                return GameStatus.WAIT_TURN

        # %% done rolling

    @staticmethod
    def receivedRacks(player: Player, network, number,
                      notify_srv_msg: default_notification,
                      notify_cln_msg: default_notification,
                      notify_racks: process_rack):

        notify_cln_msg("Your rack contains: ")
        notify_cln_msg(",".join([t.letter for t in player.get_rack_arr()]))
        notify_racks(player.get_rack_arr())

        notify_cln_msg("New letters: ")
        notify_cln_msg(",".join([t.letter for t in player.rack.get_temp_arr()]))
        notify_racks(player.rack.get_temp_arr(), temp=True)

        notify_cln_msg("Total value of your draw is: %s" % player.rack.get_temp_value())
        return GameStatus.BUY

    @staticmethod
    def buy_tiles(player: Player, network, number,
                  notify_srv_msg: default_notification,
                  notify_cln_msg: default_notification):
        Dice = "Dice: "
        Bought = "buying racks "
        Sold = "Sold: "
        get = "get"
        Iplayed = "Played"
        # %% buying
        if player.money >= player.rack.get_temp_value():
            notify_cln_msg("You have:  $%s" % player.money)
            user_ans = ""
            while user_ans.upper() != ("Y" or "N"):
                user_ans = input("Do you want to buy words? (Y-N)").upper()
                time.sleep(1)
                notify_cln_msg(f" you entered {user_ans}")
                if user_ans == "Y":
                    notify_cln_msg("user wants to buy")
                    try:
                        game = network.send(Bought)
                    except Exception as e:
                        log(e)

                    while True:
                        serverMessage = game.getServerMessage()
                        notify_srv_msg(f"{serverMessage} ")
                        if "Purchased" in serverMessage:
                            break
                        else:
                            try:
                                game = network.send(get)
                            except Exception as e:
                                continue
                    player = game.getPlayer(number)
                    notify_cln_msg("you now have $%s" % player.money)
                else:
                    break
        else:
            notify_cln_msg("You have insufficient funds to purchase tiles")

        # %% selling
        notify_cln_msg("Your rack contains: ")
        for tile in player.get_rack_arr():
            notify_cln_msg(f"{tile.letter}, {tile.score}")
        sell = input("Do you want to sell any words? Y/N ")
        if sell.upper() == "Y":
            attempt = 3
            while attempt > 0:
                wordToSell = input("input word to sell: ")

                player.sell(wordToSell)

                if player.sell_check:
                    Sold += wordToSell
                    game = network.send(Sold)
                    time.sleep(1)
                    # game = n.send(Sold)
                    # time.sleep(1)
                    while True:
                        game = network.send(get)
                        time.sleep(1)
                        serverMessage = game.getServerMessage()
                        notify_srv_msg(f"{serverMessage} ")
                        if "SOLD" in serverMessage:
                            break
                    player = game.getPlayer(number)

                    notify_cln_msg("You sold by $%s" % player.wordvalue)
                    # myPlayer.addPlayerMessage(f" sold {wordToSell}")
                    break
                else:
                    attempt -= 1
                    notify_cln_msg(
                        f"You failed to sell the word,{attempt} attempts left",
                        Colors.RED
                    )
            notify_cln_msg("You now have: $%s" % player.money)
            # %% done selling
            # sending player object to game
        game = network.send(Iplayed)
        return game
        # %%
