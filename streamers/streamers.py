#!/usr/bin/env python3

# region honeydo_list

# TODO: IINA Support
# TODO: Spin out VLC integration into it's own thing; let SL stand alone
# TODO: Add '?' flag to mirror 'h' flag behavior
# TODO: MPV support?
# TODO: 's' flag passed without Streamlink installed doesn't prompt with an error message.
# TODO: See if there is a way to make config file changes backwards compatible
# TODO: Make token refresh silent without a verbosity flag, auto rerun if token refresh is successful.
# TODO: Look into making table display customizable in terms of size (auto sizing based on window size?) or colums sortable via config file
# TODO: Documentation rework for pypi visibility. Github isn't really the focus now. Look into split documentation?

# endregion

# regions imports
import os
import configparser  # Config fun
import requests  # API fun
from pathlib import Path
import shutil  # Streamlink check
import argparse

# endregion

# region functions


def config_set(
    configDir, configPath
):  # Check if the config file is present, and if not create it with dummy values
    if not (configDir.is_dir()):
        Path.mkdir(configDir, parents=True, exist_ok=True)
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
        config["StreamLinkBits"] = {"enabled": "false"}
        with open(configPath, "w") as configfile:
            config.write(configfile)
        print(
            "Please refer to the README.md to get guidance on how to generate the needed values for the config file."
        )
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
    print("Renewing Token...")
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

def stream_link(streams, locate):
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

    streamer = streams.json()["data"][index]["user_name"]
    os.system(locate + " https://twitch.tv/" + streamer)

def config_args():
    parser = argparse.ArgumentParser(
        prog = 'Streamers',
        description="Get a list of followed Twitch live streams from the comfort of your own CLI and optionall stream them."
    )
    parser.add_argument(
        "-p",
        "--player",
        required=False,
        choices=['streamlink','iina','mpv'],
        help="Pass in your preferred player if desired. Available options: Streamlink, VLC, IINA, and MPV. Presumes you have the passed player installed and configured to take inputs via CLI.",
    )
    parser.add_argument(
        "-a",
        "--arguments",
        required=False,
        default='',
        help="Optionally pass arguments to be used with your player"
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
    #try catch to verify the selected player is installed/PATH accessable
    playerPath = shutil.which(args.player)
    if playerPath != None:
        #Start stream
        print("Starting stream")
        if args.player == "mpv":
            os.system(playerPath + " " + args.arguments + " https://twitch.tv/" + stream)

    else:
        print(args.player + " is either not installed or on the system's PATH. Please verify that it is present and retry.")
    
    #os.system(playerPath + " https://twitch.tv/" + streamer)
    #print("Player: :" + args.player + "\n playerPath + " + playerPath)

# endregion

# region main
def main():
    args = config_args()
    # region config
    configDir = Path("~/.config/streamers").expanduser()
    configFile = Path("~/.config/streamers/config").expanduser()
    config = config_set(configDir, configFile)
    # endregion
    if config["TwitchBits"]["userID"] == "foo":
        print("Quitting program. Please populate config file.")
        quit()
    streams = query_streams(config)
    
    if streams.ok:
        if len(streams.json()["data"]) > 0:
            write_results(streams, args.player)
            if args.player != None:
                player_output(args.player, streams, args)
        else:
            print("No followed streams online at this time.")
    else:
        print("Error getting stream data. Response code: " +
              str(streams.status_code))
        refresh_token(configFile, config)
        print("Attempting token refresh, please try again")
    


#streamlink --json twitch.tv/unlimitedsteam | jq -r '.streams.best.url'
#vlc --meta-title "butts" --video-title "butts" https://video-weaver.atl01.hls.ttvnw.net/v1/playlist/Cq0EgR_ErttiWkmiXFt6s7x_dRji9NBVDzN2s97SZIPxBCmh7JG5aAR-Fb4Hy4ZVUHs5ZdbCCkIBPKJO44GFanlD56O3W8sCZBeNgEmcG2sHd8t2WPOEiVlmp9J9OR60Mqd3vhNeVPhTgzzWzu12_QHtpaqmTHgV6l_v-ZBRfW8r0MZjbGYdHooLW2Puhu1CCYvBcEydAs8rREJKVIDLPj4169ovaNDICE7yRQ_anYpTyuOBmlBwMb-49n4XXZgGrdOHco4vmFblYJaB_fqVzpErd8jM1bJHg3iqNkeGuc0DGFLfW6K1Xm6NA3QMMUHgON_QLO-XoDIfuDf2IB-dkR8OaJErRmMWbRITqw64y2o7rB4WefoYcuQLngE1duUhVUsl8p0Qa0WLFs01tjThZohyISsNAOZaaesx-hANQnZQXlCBYbg7BVbQjOQTB0OMTHez79EbHCptxIruAklnvNjVdON6uPaT5nCcwn5sGhABWFyQtzih0AVzzSDVY5v5bzYS-EvuHr1iMUvWSfJKgjMNoqsX3yPzQeLHxtcwCgKvScvLwAGgQ1JgIUhcL3YMtP1C7ttQRSeQwYvsDxZnesI5xZQof8DHcjh_dFpiT8pOTKDZjix_xQoFlyhq0hRhsng0hgpPpf260EYbU1g-LSh2862JQa4lG7RkGqTgXWdGphWGGX9h2AWkC-aq5ReCQgMinaMmswleNYI8W_7sYV68AIfXx_wmvzFxrSr5Bv8aDEHgLltMofkYVMANACABKgl1cy13ZXN0LTIw-AU.m3u 
    
    
    
#    try:
#        if args.player == 'streamlink' or config["StreamLinkBits"]["enabled"].lower() == "true":
#            streamLinkFlag = True
#            print("Streamlink enabled")
#        else:
#            streamLinkFlag = False
#    except KeyError:
#        print("")
#        print(
#            "Missing ['StreamLinkBits'] section of the config file. Please refer to the documentation for an example config containing it."
#        )
#        quit()
#    if streams.ok:
#        if len(streams.json()["data"]) > 0:
#            write_results(streams, streamLinkFlag)
#            locate = shutil.which("streamlink")
#            if locate and streamLinkFlag:
#                print("")
#                stream_link(streams, locate)
#        else:
#            print("No followed streams online at this time.")
#    else:
#        print("Error getting stream data. Response code: " +
#              str(streams.status_code))
#        refresh_token(configFile, config)
#        print("Attempting token refresh, please try again")

# endregion
