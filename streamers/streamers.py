#!/usr/bin/env python3

# region honeydo_list

# TODO: See if the onbolarding process can be somewhat autoamted
# TODO: See if there is a way to make config file changes backwards compatible
# TODO: Look into making table display customizable in terms of size (auto sizing based on window size?) or colums sortable via config file
# TODO: Documentation rework for pypi visibility. Github isn't really the focus now. Look into split documentation?

# endregion

# region imports
import os
import configparser  # Config fun
import requests  # API fun
from pathlib import Path
import shutil  # Player install check
import streamlink  # Extraction of m3u8 URIs for VLC
import argparse
import logging

# endregion

# region functions


def config_set(configDir, configPath):
    if not (configDir.is_dir()):  # Check if the config dir is present, and if not create it
        Path.mkdir(configDir, parents=True, exist_ok=True)
    # Check if the config file is present, and if not create it with dummy values
    if not (configPath.is_file()):
        print("Config file not found. Creating dummy file at: " + str(configPath))
        config = configparser.ConfigParser()
        Path(configPath).touch()
        config["TwitchBits"] = {
            "userID": "foo",
            "clientID": "bar",
            "access_token": "fizz",
            "refreshToken": "buzz",
            "clientSecret": "fizzbuzz",
        }
        config["PlayerBits"] = {
            "player": "",
            "arguments": ""
        }
        with open(configPath, "w") as configfile:
            config.write(configfile)
        print(
            "Please refer to the documentation to get guidance on how to generate the needed values for the config file."
        )
    # TODO: Check for player section, add if needed
    else:
        # Populate vars
        config = configparser.RawConfigParser()
        config.read(configPath)
    return config


def config_args():
    parser = argparse.ArgumentParser(
        prog='Streamers',
        description="Get a list of followed Twitch live streams from the comfort of your own CLI and optionall stream them."
    )
    parser.add_argument(
        '-l',
        '--logging',
        help="Adds additional output/verbosity for troublshooting.",
        action="store_true"
    )
    parser.add_argument(
        "-p",
        "--player",
        required=False,
        default="",
        choices=['iina', 'mpv', 'streamlink', 'vlc'],
        help="Pass in your preferred player if desired. Available options: IINA, MPV, Streamlink, and VLC. Presumes you have the passed player installed and configured to take inputs via CLI. NOTE: CLI passed selections will override config file settngs for player, if any.",
    )
    parser.add_argument(
        "-a",
        "--arguments",
        required=False,
        type=str,
        action='store',
        # default='',
        help="Optionally pass arguments to be used with your player. HINT: Use the format: -a=\"--optional-arguments\" to pass in content with dashes so as to not conflict with argparse's parsing. WARNING: Can only be used with the -p/--player flag. Config file player arguments are seperate."
    )

    args = parser.parse_args()
    return args


def session_vars(config, args):
    sessionFlags = {
        "player": "",
        "playerFlag": False,
        "arguments": ""
    }
    """ 
        Check to see if a player has been selected in the config file and then assign it if so.
        Then, check if a player argument has been passed as an argument. If so, override the config file setting.
    """
    if not config["PlayerBits"]["player"] == "":
        sessionFlags["player"] = config["PlayerBits"]["player"]
        sessionFlags["playerFlag"] = True
    if not args.player == "":
        sessionFlags["player"] = args.player
        sessionFlags["playerFlag"] = True

    """
        This is slightly more complex. As before we default to pulling in the config file values. However, if a user passes a player via CLI, we nullify those default
        values as we don't want users crossing the streams in terms of arguments. This allows for just a player to be passed via CLI with no args to be run as default
        when the config file contains values. Finally we override again should there be a passed argument value from CLI.
    """
    if not config["PlayerBits"]["arguments"] == "":
        sessionFlags["arguments"] = config["PlayerBits"]["arguments"]
    if not args.player == "":
        sessionFlags["arguments"] = ""
    if not args.arguments == None:
        sessionFlags["arguments"] = args.arguments

    return sessionFlags


def query_streams(config):
    headers = {
        "Authorization": "Bearer " + config["TwitchBits"]["access_token"],
        "Client-Id": config["TwitchBits"]["clientID"],
    }
    data = {"user_id": config["TwitchBits"]["userID"]}
    r = requests.get(
        "https://api.twitch.tv/helix/streams/followed", params=data, headers=headers
    )
    return r


def refresh_token(configPath, config):
    logging.debug("Renewing Token...")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = (
        "grant_type=refresh_token&refresh_token="
        + config["TwitchBits"]["refreshToken"]
        + "&client_id="
        + config["TwitchBits"]["clientID"]
        + "&client_secret="
        + config["TwitchBits"]["clientSecret"]
    )
    r = requests.post("https://id.twitch.tv/oauth2/token",
                      headers=headers, data=data)
    config.set("TwitchBits", "access_token", r.json()["access_token"])
    with open(configPath, "w") as configfile:
        config.write(configfile)


def write_results(streams, player_config):
    if len(streams.json()["data"]) > 0:
        if player_config["playerFlag"] != False:
            index = 0
            print(
                "\nINDEX   CHANNEL "
                + " " * 13
                + "GAME"
                + " " * 37
                + "VIEWERS"
                + " " * 8
                + "\n"
                + "-" * 80
            )
            for stream in streams.json()["data"]:
                print(
                    "{} {} {} {}".format(
                        str(index).ljust(7),
                        stream["user_name"].ljust(20)[:20],
                        stream["game_name"].ljust(40)[:40],
                        str(stream["viewer_count"]).ljust(8),
                    )
                )
                index += 1
        else:
            print(
                "\nCHANNEL "
                + " " * 13
                + "GAME"
                + " " * 37
                + "VIEWERS"
                + " " * 8
                + "\n"
                + "-" * 80
            )
            for stream in streams.json()["data"]:
                print(
                    "{} {} {}".format(
                        stream["user_name"].ljust(20)[:20],
                        stream["game_name"].ljust(40)[:40],
                        str(stream["viewer_count"]).ljust(8),
                    )
                )
    else:
        print("No followed streams online at this time.")


def player_selection(player_config, streams):
    while True:
        try:
            maxSel = len(streams.json()["data"])
            index = -1
            while index not in range(0, maxSel):
                index = int(input("Enter index of stream to watch: "))
        except ValueError:
            print(
                "Sorry, I didn't understand that. Enter an integer from 0 to "
                + str(maxSel - 1)
            )
            continue
        except KeyboardInterrupt:
            quit()
        else:
            break
    stream = streams.json()["data"][index]["user_name"]
    start_player(stream, player_config)


def start_player(stream, player_config):
    playerPath = shutil.which(player_config["player"])
    if playerPath != None:
        # Start stream
        print("----------Starting stream----------")
        if player_config["player"] == "mpv" or player_config["player"] == "streamlink" or player_config["player"] == "iina":
            logging.debug("Starting " + player_config["player"] + " with command: " + playerPath +
                          " " + player_config["arguments"] + " https://twitch.tv/" + stream)
            os.system(playerPath + " " + player_config["arguments"] +
                      " https://twitch.tv/" + stream)
        elif player_config["player"] == "vlc":
            streams = streamlink.streams("https://twitch.tv/" + stream)
            logging.debug("Starting " + player_config["player"] + " with command: " +
                          playerPath + " " + player_config["arguments"] + " " + streams["best"].url)
            os.system(playerPath + " --meta-title \"" + stream + "\" --video-title \"" +
                      stream + "\" " + player_config["arguments"] + " " + streams["best"].url)

    else:
        print(player_config["player"] +
              " is either not installed or on the system's PATH. Please verify that it is present and retry.")

# endregion

# region main


def main():
    args = config_args()
    if args.logging:
        logging.basicConfig(format='DEBUG: %(message)s', level=logging.DEBUG)
    # region config
    configDir = Path("~/.config/streamers").expanduser()
    configFile = Path("~/.config/streamers/config").expanduser()
    config = config_set(configDir, configFile)
    if config["TwitchBits"]["userID"] == "foo":
        print("Quitting program. Please populate config file.")
        quit()
    # endregion
    player_config = session_vars(config, args)

    streams = query_streams(config)

    if not streams.ok:
        logging.debug("Attempting token refresh.")
        refresh_token(configFile, config)
        streams = query_streams(config)
    # region logging
    logging.debug("Config file player settings:\n Player: " +
                  config["PlayerBits"]["player"] + "\n Arguments: " + config["PlayerBits"]["arguments"])
    logging.debug("Argparse player settings: \n Player: " +
                  args.player + "\n Arguments: " + str(args.arguments))
    logging.debug("Player setting: " + player_config["player"])
    logging.debug("Player arguments: " + player_config["arguments"])
    logging.debug("playerFlag: " + str(player_config["playerFlag"]))
    # endregion

    if streams.ok:
        write_results(streams, player_config)
        if player_config["playerFlag"] != False:
            player_selection(player_config, streams)
    else:
        print("Error getting stream data. Response code: " +
              str(streams.status_code))

# endregion
