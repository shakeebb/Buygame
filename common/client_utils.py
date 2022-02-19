from common.game import Game, Txn
from common.tile import Tile
from common.player import Player
import time
from common.gameconstants import ClientMsgReq, GameUIStatus, Colors, ClientResp
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
                          cur_game_status: GameUIStatus,
                          notify_srv_msg: default_notification,
                          messagebox_notify: default_notification):
        # check if we rolled dice yet
        if game.rolled is True:
            # leader rolled
            serverMessage = game.get_server_message()
            notify_srv_msg(serverMessage)

            # %% racks are handed
            if ClientResp.Racks_Ready.msg in serverMessage:
                return GameUIStatus.RECEIVE_RACKS
        # %%
        elif game.isReady():
            # we have not rolled dice
            # if number == game.leader:
            if number == game.currentPlayer:
                # it is my turn to roll
                messagebox_notify("It is your turn to roll dice")
                return GameUIStatus.ROLL_DICE
            # %% some one else is playing
            else:
                # it is someone else's turn to roll but don't notify
                # when already notified once.
                if cur_game_status != GameUIStatus.WAIT_TURN:
                    messagebox_notify(f"Player {game.getPlayer(game.currentPlayer).name} needs to roll")
                return GameUIStatus.WAIT_TURN

        # %% done rolling

    @staticmethod
    def rack_to_str(rack: [Tile]):
        return ",".join(t.letter if t is not None else "" for t in rack)

    @staticmethod
    def receive_racks(player: Player, game_status: GameUIStatus, number,
                      notify_srv_msg: default_notification,
                      notify_cln_msg: default_notification,
                      messagebox_notify: default_notification,
                      notify_racks: process_rack):

        # notify_cln_msg("Your rack contains: ")
        # notify_cln_msg(ClientUtils.rack_to_str(player.get_rack_arr()))
        notify_racks(player.get_rack_arr())

        # notify_cln_msg("New letters: ")
        # notify_cln_msg(ClientUtils.rack_to_str(player.rack.get_temp_arr()))
        notify_racks(player.rack.get_temp_arr(), temp=True)

        if game_status == GameUIStatus.RECEIVE_RACKS:
            if player.money >= player.rack.get_temp_value():
                messagebox_notify(f"Buy {ClientUtils.rack_to_str(player.rack.get_temp_arr())} "
                                  f"for ${player.rack.get_temp_value()} ")
            else:
                messagebox_notify(f"Insufficient balance ${player.money} "
                                  f"need ${player.rack.get_temp_value()} ", Colors.RED)

    @staticmethod
    def buy_tiles(game: Game, network, number,
                  notify_srv_msg: default_notification,
                  notify_cln_msg: default_notification,
                  messagebox_notify: default_notification
                  ) -> (GameUIStatus, Game):
        notify_cln_msg("user wants to buy")
        # try:
        ret_game: Game = network.send(ClientMsgReq.Buy.msg)
        assert ret_game is not None
        game = ret_game
        # except Exception as e:
        #     log(e)
        #     return GameStatus.ERROR, None
        player: Player = game.players()[number]
        serverMessage = game.get_server_message()
        notify_srv_msg(f"{serverMessage} ")
        if ClientResp.Bought.msg in serverMessage:
            notify_cln_msg("bought. you now have $%s" % player.money)
            # messagebox_notify(f"Bought. You have ${player.money} ", Colors.GREEN)
            return GameUIStatus.BOUGHT, game
        else:
            notify_cln_msg(f"- Buy failed. You have ${player.money} ", Colors.RED)
            return GameUIStatus.BUY_FAILED, game

    @staticmethod
    def skip_buy(game: Game, network: Network,
                 notify_srv_msg: default_notification,
                 notify_cln_msg: default_notification):
        ret_game = network.send(ClientMsgReq.Skip_Buy.msg)
        assert ret_game is not None and isinstance(ret_game, Game)
        game = ret_game
        serverMessage = game.get_server_message()
        notify_srv_msg(f"{serverMessage} ")
        if ClientResp.Buy_Skipped.msg in serverMessage:
            notify_cln_msg("Buy cancelled.")
            return GameUIStatus.BUY_CANCELLED, game
        else:
            notify_cln_msg("Buy couldn't be cancelled.")
            return GameUIStatus.BUY_CANCEL_FAILED, game

    @staticmethod
    def sell_word(game: Game, network, number, word_to_sell,
                  notify_srv_msg: default_notification,
                  notify_cln_msg: default_notification,
                  messagebox_notify: default_notification):
        selling = ClientMsgReq.Sell.msg
        ret_status = GameUIStatus.SELL_FAILED
        # %% selling
        # attempt = 3
        # while attempt > 0:
        # player.sell(word_to_sell)

        # if player.sell_check:
        try_selling = selling + word_to_sell
        ret_game = network.send(try_selling)
        assert ret_game is not None
        game = ret_game
        notify_srv_msg(f"{game.get_server_message()} ")
        # time.sleep(1)
        player: Player = game.players()[number]
        # serverMessage = game.get_server_message()
        if player.txn_status == Txn.SOLD:
            ret_status = GameUIStatus.SHOW_SELL
        # elif player.txn_status == Txn.SELL_CANCELLED_SELL_AGAIN:
        #     ret_status = GameUIStatus.SELL_AGAIN
        else:
            # attempt -= 1
            notify_cln_msg(
                f"You failed to sell the word",
                Colors.RED
            )
            # messagebox_notify(f"Sell failed. You have ${player.money}", Colors.RED)
            ret_status = GameUIStatus.SHOW_SELL

        notify_cln_msg("You now have: $%s" % player.money)
        # %% done selling
        return ret_status, game

    @staticmethod
    def discard_sell(network: Network, discarded_word: str,
                     notify_srv_msg: default_notification,
                     notify_cln_msg: default_notification):
        ret_game = network.send(ClientMsgReq.Discard_Sell.msg + discarded_word)
        assert ret_game is not None and isinstance(ret_game, Game)
        game = ret_game
        serverMessage = game.get_server_message()
        notify_srv_msg(f"{serverMessage} ")
        ret_status = None
        if ClientResp.Sell_Discarded.msg in serverMessage:
            notify_cln_msg("Sell cancelled")
            ret_status = GameUIStatus.SHOW_SELL
        else:
            notify_cln_msg("Sell couldn't be cancelled.")

        return ret_status, game

    @staticmethod
    def end_turn(network: Network,
                 notify_srv_msg: default_notification,
                 notify_cln_msg: default_notification):
        ret_game = network.send(ClientMsgReq.EndTurn.msg)
        assert ret_game is not None and isinstance(ret_game, Game)
        game = ret_game
        serverMessage = game.get_server_message()
        notify_srv_msg(f"{serverMessage} ")
        ret_status = None
        if ClientResp.Turn_Ended.msg in serverMessage:
            notify_cln_msg("Turn Ended")
            ret_status = GameUIStatus.I_PLAYED
        elif ClientResp.Must_Sell.msg in serverMessage:
            notify_cln_msg("Must sell")
            ret_status = GameUIStatus.SHOW_SELL

        return ret_status, game

    @staticmethod
    def i_played(cur_round: int, network: Network):
        # sending player object to game
        game = network.send(ClientMsgReq.Played.msg + str(cur_round))
        return GameUIStatus.TURN_COMPLETE, game
        # %%

    @staticmethod
    def round_done(cur_round: int, network: Network,
                   notify_client: default_notification,
                   messagebox_notify: default_notification
                   ):
        game = network.send(ClientMsgReq.Is_Done.msg + str(cur_round))
        assert isinstance(game, Game)
        if ClientResp.Done.msg in game.get_server_message():
            messagebox_notify(f"Round {cur_round} complete.", Colors.DIRTY_YELLOW)
            cur_round = game.turn
            return GameUIStatus.PLAY, cur_round, game
        elif ClientResp.Not_Ready.msg in game.get_server_message():
            notify_client(game.get_server_message(), Colors.RED)
            return GameUIStatus.WAIT_ALL_PLAYED, cur_round, game
