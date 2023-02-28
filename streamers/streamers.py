#!/usr/bin/env python3
# regions imports
import os
import configparser  # Config fun
import requests  # API fun
from pathlib import Path
import shutil  # Streamlink check
import argparse
from typing import Dict, List, Any, Optional, Tuple
# endregion

# region functions
def config_set(
    config_dir: Path, config_path: Path
) -> List[str]:
    """Check if the config file is present, and if not create it with dummy values"""
    if not config_dir.is_dir():
        Path.mkdir(config_dir, parents=True, exist_ok=True)
    if not config_path.is_file():
        print("Config file not found. Creating dummy file at: " + str(config_path))
        config = configparser.ConfigParser()
        Path(config_path).touch()
        config["TwitchBits"] = {
            "userID": "foo",
            "clientID": "bar",
            "access_token": "fizz",
            "refreshToken": "buzz",
            "clientSecret": "fizzbuzz",
        }
        config["StreamLinkBits"] = {"enabled": "false"}
        with open(config_path, "w", encoding="utf-8") as configfile:
            config.write(configfile)
        print(
            "Please refer to the README.md to get guidance on how to generate the needed values for the config file."
        )
    else:
        # Populate vars
        config = configparser.RawConfigParser()
        config.read(config_path)
    return config


def query_streams(config: Dict[str, Any]) -> Tuple[bool, int, Dict[str, Any]]:
    """Performs a rest query to twitch to query stream statistics"""
    headers = {
        "Authorization": "Bearer " + config["TwitchBits"]["access_token"],
        "Client-Id": config["TwitchBits"]["clientID"],
    }
    data = {"user_id": config["TwitchBits"]["userID"]}
    r = requests.get(
        "https://api.twitch.tv/helix/streams/followed", params=data, headers=headers
    )
    return r.ok, r.status_code, r.json()


def refresh_token(config_path: Path, config: Dict[str, Any]) -> None:
    """Performs a rest query to twitch to refresh the authorization token"""
    print("Renewing Token...")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": config["TwitchBits"]["refreshToken"],
        "client_id": config["TwitchBits"]["clientID"],
        "client_secret": config["TwitchBits"]["clientSecret"]
    }
    r = requests.post("https://id.twitch.tv/oauth2/token", headers=headers, data=data)
    config.set("TwitchBits", "access_token", r.json()["access_token"])
    with open(config_path, "w", encoding="utf-8") as configfile:
        config.write(configfile)


def write_results(streams: Dict[str, Any], stream_link_flag: bool) -> None:
    """Writes useful stats to the terminal"""
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
    if stream_link_flag:
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
                "{} {} {}".format(
                    stream["user_name"].ljust(20)[:20],
                    stream["game_name"].ljust(40)[:40],
                    str(stream["viewer_count"]).ljust(8),
                )
            )


def stream_link(streams: Dict[str, Any], locate: str) -> None:
    """Launches a twitch stream using the full path to streamlink."""
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

    streamer = streams["data"][index]["user_name"]
    os.system(f"{locate} https://twitch.tv/{streamer}")


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
    config_dir = Path("~/.config/streamers").expanduser()
    config_file = Path("~/.config/streamers/config").expanduser()
    config = config_set(config_dir, config_file)
    # endregion
    # Deadman's switch
    if config["TwitchBits"]["userID"] == "foo":
        print("Quitting program. Please populate config file.")
        quit()
    stream_ok, status_code, streams = query_streams(config)
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
    if stream_ok:
        if len(streams["data"]) > 0:
            write_results(streams, streamLinkFlag)
            locate = shutil.which("streamlink")
            if locate and streamLinkFlag:
                print("")
                stream_link(streams, locate)
        else:
            print("No followed streams online at this time.")
    else:
        print(f"Error getting stream data. Response code: {status_code}")
        refresh_token(config_file, config)
        print("Attempting token refresh, please try again")


# endregion
