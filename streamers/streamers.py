#!/usr/bin/env python3

# region honeydo_list

# TODO: See if the onbolarding process can be somewhat autoamted
# TODO: See if there is a way to make config file changes backwards compatible
# TODO: Look into making table display customizable in terms of size (auto sizing based on window size?) or colums sortable via config file
# TODO: Documentation rework for pypi visibility. Github isn't really the focus now. Look into split documentation?

# endregion

# region imports
import os
from configparser import ConfigParser  # Config fun
import requests  # API fun
from pathlib import Path
import shutil  # Player install check
import streamlink  # Extraction of m3u8 URIs for VLC
import argparse
import logging
from typing import List, Dict, Optional, Any, Tuple, Union

# endregion

# region functions

CONFIG_SCHEMA: Dict[str, Dict[str, str]] = {
    "TwitchBits": {
        "userID": "foo",
        "clientID": "bar",
        "access_token": "fizz",
        "refreshToken": "buzz",
        "clientSecret": "fizzbuzz",
    },
    "PlayerBits": {
        "player": "",
        "arguments": ""
    }
}

def config_set(config_path: Path) -> ConfigParser:
    """
    Load our config file as described in `CONFIG_SCHEMA`. If this file does not
    exist, attempt to create the file and inform the user that they need to
    perform configuration as described in the README.

    :params config_path: A path object pointing at our configuration file. In
    the event only a directory is specified then this will default to
    `$directory/config`.
    """
    if not config_path:
        raise RuntimeError("Configuration file not specified!")

    # Checks if our config path is a directory,
    # if it is a directory, default to a file named 'config'
    config_file = ""
    if config_path.is_dir():  # Check if the config dir is present, and if not create it
        Path.mkdir(config_path, parents=True, exist_ok=True)
        config_file = "config"

    # If our specified file doesn't exist, mkdir our directory
    if not config_path.exists():
        Path.mkdir(Path(os.path.dirname(config_path)), parents=True, exist_ok=True)

    config_filepath = Path(os.path.join(config_path, config_file))

    # Check if the config file is present, and if not create it with dummy values
    if not config_filepath.is_file():
        print(f"Config file not found. Creating dummy file at: {config_filepath}")
        config = ConfigParser()
        config.read_dict(CONFIG_SCHEMA)
        with open(config_filepath, "w", encoding="utf-8") as file:
            config.write(file)
        print(
            "Please refer to the documentation to get guidance on how to generate the needed values for the config file."
        )
        exit(1)
    # TODO: Check for player section, add if needed
    # Populate vars
    config = ConfigParser(interpolation=None)
    config.read(config_filepath)
    return config


def config_args() -> argparse.Namespace:
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


def session_vars(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
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


def query_streams(config: Dict[str, Any]) -> Tuple[bool, int, Dict[str, Any]]:
    headers = {
        "Authorization": "Bearer " + config["TwitchBits"]["access_token"],
        "Client-Id": config["TwitchBits"]["clientID"],
    }
    data = {"user_id": config["TwitchBits"]["userID"]}
    r = requests.get(
        "https://api.twitch.tv/helix/streams/followed", params=data, headers=headers
    )
    return r.ok, r.status_code, r.json()


def refresh_token(config_path: Path, config: ConfigParser) -> None:
    logging.debug("Renewing Token...")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": config["TwitchBits"]["refreshToken"],
        "client_id": config["TwitchBits"]["clientID"],
        "client_secret": config["TwitchBits"]["clientSecret"]
    }
    r = requests.post("https://id.twitch.tv/oauth2/token",
                      headers=headers, data=data)
    config.set("TwitchBits", "access_token", r.json()["access_token"])
    with open(config_path, "w", encoding="utf-8") as config_file:
        config.write(config_file)


def write_results(streams: Dict[str, Any], player_config: Dict[str, Any]) -> None:
    table_header = (
                "\nINDEX   CHANNEL "
                + " " * 13
                + "GAME"
                + " " * 37
                + "VIEWERS"
                + " " * 8
                + "\n"
                + "-" * 80
            )

    if len(streams["data"]) > 0:
        if player_config["playerFlag"] != False:
            index = 0
            print(table_header)
            for stream in streams["data"]:
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
            print(table_header)
            for stream in streams["data"]:
                print(
                    "{} {} {} {}".format(
                        " " * 7,
                        stream["user_name"].ljust(20)[:20],
                        stream["game_name"].ljust(40)[:40],
                        str(stream["viewer_count"]).ljust(8),
                    )
                )
    else:
        print("No followed streams online at this time.")


def player_selection(player_config: Dict[str, Any], streams: Dict[str, Any]):
    while True:
        try:
            maxSel = len(streams["data"])
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
    stream = streams["data"][index]["user_name"]
    start_player(stream, player_config)


def start_player(stream: str, player_config: Dict[str, Any]):
    playerPath = shutil.which(player_config["player"])
    if playerPath:
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
    config_dir = Path("~/.config/streamers").expanduser()
    config_file = "config"
    config_filepath = config_dir + config_file
    config = config_set(config_filepath)
    if config["TwitchBits"]["userID"] == "foo":
        print("Quitting program. Please populate config file.")
        quit()
    # endregion
    player_config = session_vars(config, args)

    query_ok, query_status, streams = query_streams(config)

    if not query_ok:
        logging.debug("Attempting token refresh.")
        refresh_token(config_filepath, config)
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

    if query_ok:
        write_results(streams, player_config)
        if player_config["playerFlag"]:
            player_selection(player_config, streams)
    else:
        print("Error getting stream data. Response code: " +
              str(query_status))

# endregion
