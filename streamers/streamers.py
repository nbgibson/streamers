#!/usr/bin/env python3
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
    r = requests.post("https://id.twitch.tv/oauth2/token", headers=headers, data=data)
    config.set("TwitchBits", "access_token", r.json()["access_token"])
    with open(configPath, "w") as configfile:
        config.write(configfile)


def write_results(streams, streamLinkFlag):
    if streamLinkFlag:
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


# endregion

# region main
def main():
    # region parser
    parser = argparse.ArgumentParser(
        description="Get a list of followed Twitch live streams from the comfort of your own CLI."
    )
    parser.add_argument(
        "-s",
        "--streamlink",
        action="store_true",
        help="flag to enable streamlink functionality (if installed)",
    )
    args = parser.parse_args()
    # endregion
    # region config
    configDir = Path("~/.config/streamers").expanduser()
    configFile = Path("~/.config/streamers/config").expanduser()
    config = config_set(configDir, configFile)
    # endregion
    # Deadman's switch
    if config["TwitchBits"]["userID"] == "foo":
        print("Quitting program. Please populate config file.")
        quit()
    streams = query_streams(config)
    try:
        if args.streamlink or config["StreamLinkBits"]["enabled"].lower() == "true":
            streamLinkFlag = True
        else:
            streamLinkFlag = False
    except KeyError:
        print("")
        print(
            "Missing ['StreamLinkBits'] section of the config file. Please refer to the documentation for an example config containing it."
        )
        quit()
    if streams.ok:
        if len(streams.json()["data"]) > 0:
            write_results(streams, streamLinkFlag)
            locate = shutil.which("streamlink")
            if locate and streamLinkFlag:
                print("")
                stream_link(streams, locate)
        else:
            print("No followed streams online at this time.")
    else:
        print("Error getting stream data. Response code: " + str(streams.status_code))
        refresh_token(configFile, config)
        print("Attempting token refresh, please try again")


# endregion
