#!/usr/bin/env python3

# region honeydo_list

# TODO: Set up config file structure to use player and args data
# TODO: Set user passed CLI flags to override config file settings
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
    if not (configDir.is_dir()): # Check if the config dir is present, and if not create it 
        Path.mkdir(configDir, parents=True, exist_ok=True)
    if not (configPath.is_file()): # Check if the config file is present, and if not create it with dummy values
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


def write_results(streams, playerFlag):
    if len(streams.json()["data"]) > 0:
        if playerFlag != None:
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
        choices=['iina', 'mpv', 'streamlink', 'vlc'],
        help="Pass in your preferred player if desired. Available options: Streamlink, IINA, and MPV. Presumes you have the passed player installed and configured to take inputs via CLI.",
    )
    parser.add_argument(
        "-a",
        "--arguments",
        required=False,
        type=str,
        action='store',
        default='',
        help="Optionally pass arguments to be used with your player. HINT: Use the format: -a=\"--optional-arguments\" to pass in content with dashes so as to not conflict with argparse's parsing."
    )

    args = parser.parse_args()
    return args


def player_output(player, streams, args):
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
    start_player(stream, args)


def start_player(stream, args):
    playerPath = shutil.which(args.player)
    if playerPath != None:
        # Start stream
        print("----------Starting stream----------")
        if args.player == "mpv" or args.player == "streamlink" or args.player == "iina":
            logging.debug("Starting " + args.player + " with command: " + playerPath +
                  " " + args.arguments + " https://twitch.tv/" + stream)
            os.system(playerPath + " " + args.arguments +
                      " https://twitch.tv/" + stream)
        elif args.player == "vlc":
            streams = streamlink.streams("https://twitch.tv/" + stream)
            logging.debug("Starting " + args.player + " with command: " +
                  playerPath + " " + args.arguments + " " + streams["best"].url)
            os.system(playerPath + " --meta-title \"" + stream + "\" --video-title \"" +
                      stream + "\" " + args.arguments + " " + streams["best"].url)

    else:
        print(args.player + " is either not installed or on the system's PATH. Please verify that it is present and retry.")

# endregion

# region main

def main():
    args = config_args()
    if args.logging:
        logging.basicConfig(format='DEBUG: %(message)s',level=logging.DEBUG)
    # region config
    configDir = Path("~/.config/streamers").expanduser()
    configFile = Path("~/.config/streamers/config").expanduser()
    config = config_set(configDir, configFile)
    # endregion
    if config["TwitchBits"]["userID"] == "foo":
        print("Quitting program. Please populate config file.")
        quit()
    streams = query_streams(config)

    if not streams.ok:
        logging.debug("Attempting token refresh.")
        refresh_token(configFile, config)

    if streams.ok:
        write_results(streams, args.player)
        if args.player != None:
            player_output(args.player, streams, args)
    else:
        print("Error getting stream data. Response code: " +
              str(streams.status_code))

# endregion