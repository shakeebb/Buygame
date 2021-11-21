
from common.game import Game, Player, Tile
import time
from common.gameconstants import ClientMsgReq, GameStatus, Colors, ClientResp
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
                          cur_game_status: GameStatus,
                          notify_srv_msg: default_notification,
                          notify_cln_msg: default_notification):
        # check if we rolled dice yet
        if game.rolled is True:
            # leader rolled
            serverMessage = game.getServerMessage()
            notify_srv_msg(serverMessage)

            # %% racks are handed
            if ClientResp.Racks_Ready.msg in serverMessage:
                return GameStatus.RECEIVE_RACKS
        # %%
        else:
            # we have not rolled dice
            # if number == game.leader:
            if number == game.currentPlayer:
                # it is my turn to roll
                notify_cln_msg("It is your turn to roll dice")
                return GameStatus.ROLL_DICE
            # %% some one else is playing
            else:
                # it is someone else's turn to roll but don't notify
                # when already notified once.
                if cur_game_status != GameStatus.WAIT_TURN:
                    notify_cln_msg(f"Player {game.leader + 1} needs to roll")
                return GameStatus.WAIT_TURN

        # %% done rolling

    @staticmethod
    def rack_to_str(rack: [Tile]):
        return ",".join(t.letter if t is not None else "" for t in rack)

    @staticmethod
    def receive_racks(player: Player, network, number,
                      notify_srv_msg: default_notification,
                      notify_cln_msg: default_notification,
                      notify_racks: process_rack):

        notify_cln_msg("Your rack contains: ")
        notify_cln_msg(ClientUtils.rack_to_str(player.get_rack_arr()))
        notify_racks(player.get_rack_arr())

        notify_cln_msg("New letters: ")
        notify_cln_msg(ClientUtils.rack_to_str(player.rack.get_temp_arr()))
        notify_racks(player.rack.get_temp_arr(), temp=True)

        notify_cln_msg("Total value of your draw is: %s" % player.rack.get_temp_value())
        if player.money >= player.rack.get_temp_value():
            notify_cln_msg("You have:  $%s" % player.money)
        else:
            notify_cln_msg("You have insufficient funds to purchase tiles", Colors.RED)

    @staticmethod
    def buy_tiles(game: Game, network, number,
                  notify_srv_msg: default_notification,
                  notify_cln_msg: default_notification) -> (GameStatus, Game):
        notify_cln_msg("user wants to buy")
        # try:
        ret_game: Game = network.send(ClientMsgReq.Buy.msg)
        assert ret_game is not None
        game = ret_game
        # except Exception as e:
        #     log(e)
        #     return GameStatus.ERROR, None
        serverMessage = game.getServerMessage()
        notify_srv_msg(f"{serverMessage} ")
        if ClientResp.Bought.msg in serverMessage:
            player = game.getPlayer(number)
            notify_cln_msg("you now have $%s" % player.money)
            return GameStatus.BOUGHT, game
        else:
            return GameStatus.BUY_FAILED, game

    @staticmethod
    def cancel_buy(game: Game, network: Network,
                   notify_srv_msg: default_notification,
                   notify_cln_msg: default_notification):
        ret_game = network.send(ClientMsgReq.Cancel_Buy.msg)
        assert ret_game is not None and isinstance(ret_game, Game)
        game = ret_game
        serverMessage = game.getServerMessage()
        notify_srv_msg(f"{serverMessage} ")
        if ClientResp.Buy_Cancelled.msg in serverMessage:
            notify_cln_msg("Buy cancelled.")
        else:
            notify_cln_msg("Buy couldn't be cancelled.")

        return GameStatus.ENABLE_SELL, game

    @staticmethod
    def sell_word(game: Game, network, number, word_to_sell,
                  notify_srv_msg: default_notification,
                  notify_cln_msg: default_notification):
        selling = ClientMsgReq.Sell.msg
        ret_status = GameStatus.SELL_FAILED
        # %% selling
        # attempt = 3
        # while attempt > 0:
            # player.sell(word_to_sell)

        # if player.sell_check:
        try_selling = selling + word_to_sell
        ret_game = network.send(try_selling)
        assert ret_game is not None
        game = ret_game
        # time.sleep(1)
        player: Player = game.getPlayer(number)
        serverMessage = game.getServerMessage()
        if player.sell_check:
            notify_srv_msg(f"{serverMessage} ")
            if ClientResp.Sold.msg in serverMessage:
                ret_status = GameStatus.SOLD
            player = game.getPlayer(number)
            notify_cln_msg("You sold by $%s" % player.wordvalue)
            # break
        else:
            # attempt -= 1
            notify_cln_msg(
                f"You failed to sell the word",
                Colors.RED
            )
            ret_status = GameStatus.SELL_FAILED

        player: Player = game.getPlayer(number)
        notify_cln_msg("You now have: $%s" % player.money)
        # %% done selling
        return ret_status, game

    @staticmethod
    def i_played(cur_round: int, network: Network):
        # sending player object to game
        game = network.send(ClientMsgReq.Played.msg + str(cur_round))
        return GameStatus.TURN_COMPLETE, game
        # %%

    @staticmethod
    def round_done(cur_round: int, network: Network,
                   notify_client: default_notification):
        game = network.send(ClientMsgReq.Is_Done.msg + str(cur_round))
        assert isinstance(game, Game)
        if ClientResp.Done.msg in game.getServerMessage():
            notify_client(f"round {cur_round} done, time for next round ")
            cur_round = game.turn
            return GameStatus.PLAY, cur_round, game
        elif ClientResp.Not_Ready.msg in game.getServerMessage():
            notify_client(game.getServerMessage())
            return GameStatus.WAIT_ALL_PLAYED, cur_round, game

