#!/usr/bin/env python3

# region honeydo_list

# TODO: Argument to bypass/clear player settings for a pure query``
# TODO: Pyinput Plus input handling (SimpleTermMenu may be a better option.)
# TODO: See if the onboarding process can be somewhat automated (Yes, it can.)
# TODO: See if there is a way to make config file changes backwards compatible
# TODO: Look into making table display customizable in terms of size (auto sizing based on window size?) or colums sortable via config file
# TODO: Documentation rework for pypi visibility. Github isn't really the focus now. Look into split documentation?
# TODO: Chromecast integration
# TODO: Full rewrite to make this all less of a mess

# endregion

# region imports d
import os
from configparser import ConfigParser  # Config fun
import requests  # API fun
from pathlib import Path
import shutil  # Player install check
import streamlink  # Extraction of m3u8 URIs for VLC
import argparse
import logging
from importlib.metadata import version
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
    "PlayerBits": {"player": "", "arguments": ""},
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
    # Populate vars
    config = ConfigParser(interpolation=None)
    config.read(config_filepath)
    return config


def config_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="Streamers",
        description="Get a list of followed Twitch live streams from the comfort of your own CLI and optionall stream them.",
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Returns the version of streamers you have installed.",
        action="store_true",
    )
    parser.add_argument(
        "-l",
        "--logging",
        help="Adds additional output/verbosity for troublshooting.",
        action="store_true",
    )
    parser.add_argument(
        "-p",
        "--player",
        required=False,
        default="",
        choices=["iina", "mpv", "streamlink", "vlc"],
        help="Pass in your preferred player if desired. Available options: IINA, MPV, Streamlink, and VLC. Presumes you have the passed player installed and configured to take inputs via CLI. NOTE: CLI passed selections will override config file settngs for player, if any.",
    )
    parser.add_argument(
        "-a",
        "--arguments",
        required=False,
        type=str,
        action="store",
        # default='',
        help='Optionally pass arguments to be used with your player. HINT: Use the format: -a="--optional-arguments" to pass in content with dashes so as to not conflict with argparse\'s parsing. WARNING: Can only be used with the -p/--player flag. Config file player arguments are seperate.',
    )

    args = parser.parse_args()
    return args


def session_vars(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """
    Generates our session flags from our configuration file and our launch args.
    """

    sessionFlags = {"player": "", "playerFlag": False, "arguments": ""}
    # Check to see if a player has been selected in the config file and then
    # assign it if so. Then, check if a player argument has been passed as an
    # argument. If so, override the config file setting.
    if config["PlayerBits"]["player"]:
        sessionFlags["player"] = config["PlayerBits"]["player"]
        sessionFlags["playerFlag"] = True
    if args.player:
        sessionFlags["player"] = args.player
        sessionFlags["playerFlag"] = True

    # This is slightly more complex. As before we default to pulling in the
    # config file values. However, if a user passes a player via CLI, we nullify
    # those default values as we don't want users crossing the streams in terms
    # of arguments. This allows for just a player to be passed via CLI with no
    # args to be run as default when the config file contains values. Finally we
    # override again should there be a passed argument value from CLI.
    if config["PlayerBits"]["arguments"]:
        sessionFlags["arguments"] = config["PlayerBits"]["arguments"]
    if args.player:
        sessionFlags["arguments"] = ""
    if args.arguments:
        sessionFlags["arguments"] = args.arguments

    return sessionFlags


def query_streams(config: Dict[str, Any]) -> Tuple[bool, int, Dict[str, Any]]:
    """
    Performs a GET query to Twitch to find followed users.

    Returns a tuple starting with the boolean of the HTTP request success,
    followed by the HTTP status code of the request, followed by a dict
    containing the JSON response from Twitch.
    """
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
    """
    Refreshes our authorization token from Twitch.
    """
    logging.debug("Renewing Token...")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": config["TwitchBits"]["refreshToken"],
        "client_id": config["TwitchBits"]["clientID"],
        "client_secret": config["TwitchBits"]["clientSecret"],
    }
    r = requests.post("https://id.twitch.tv/oauth2/token", headers=headers, data=data)
    logging.debug(f"Response JSON: \n\t{r.json()}")
    config.set("TwitchBits", "access_token", r.json()["access_token"])
    with open(config_path, "w", encoding="utf-8") as config_file:
        config.write(config_file)


def write_results(streams: Dict[str, Any], player_config: Dict[str, Any] = {}) -> bool:
    """
    Prints the status of our subscribed Twitch channels to console.

    If no streams subscribed by the user are online, returns false.
    """

    if len(streams["data"]) > 0:
        if player_config["playerFlag"] != False:
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
            table_header = (
                "\nCHANNEL "
                + " " * 13
                + "GAME"
                + " " * 16  # 37
                + "VIEWERS"
                + " " * 3
                + "\n"
                + "-" * 50
            )
            print(table_header)
            for stream in streams["data"]:
                print(
                    f"{stream['user_name'].ljust(20)[:20]} {stream['game_name'].ljust(19)[:19]} {str(stream['viewer_count']).ljust(8)}"
                )
    else:
        print("No followed streams online at this time.")
        return False
    return True


def player_selection(player_config: Dict[str, Any], streams: Dict[str, Any]):
    """
    Prompts the user to select a stream based on the index displayed in
    `write_results()`.
    """
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


def start_player(stream: str, player_config: Dict[str, Any]) -> bool:
    """
    Launches a media player connected a specific twitch stream.

    If the user's media player is not found or is unsupported then return false.
    """
    playerPath = shutil.which(player_config["player"])
    if playerPath:
        # Start stream
        print("----------Starting stream----------")
        if player_config["player"] in ["mpv", "streamlink", "iina"]:
            logging.debug(
                f"Starting {player_config['player']} with command: {playerPath} {player_config['arguments']} https://twitch.tv/{stream}"
            )
            os.system(
                f"{playerPath} {player_config['arguments']} https://twitch.tv/{stream}"
            )
        elif player_config["player"] in ["vlc"]:
            streams = streamlink.streams(f"https://twitch.tv/{stream}")
            logging.debug(
                f"Starting {player_config['player']} with command: {playerPath} {player_config['arguments']} {streams['best'].url}"
            )
            os.system(
                f"{playerPath} --meta-title \"{stream}\" --video-title \"{stream}\" {player_config['arguments']} {streams['best'].url}"
            )
        else:
            print(f"{player_config['player']} is not currently supported at this time")
            return False
    else:
        print(
            player_config["player"]
            + " is either not installed or on the system's PATH. Please verify that it is present and retry."
        )
        return False
    return True


# endregion

# region main


def main():
    """
    Entrypoint of script.
    """
    args = config_args()
    if args.version:
        print(f"{version('streamers')}")
        quit()
    if args.logging:
        logging.basicConfig(format="DEBUG: %(message)s", level=logging.DEBUG)
    # region config
    config_dir = Path("~/.config/streamers").expanduser()
    config_file = "config"
    config_filepath = config_dir / config_file
    config = config_set(config_filepath)
    if config["TwitchBits"]["userID"] == CONFIG_SCHEMA["TwitchBits"]["userID"]:
        print(
            "Default settings detected. Quitting program. Please populate config file."
        )
        quit()
    # endregion
    player_config = session_vars(config, args)

    query_ok, query_status, streams = query_streams(config)
    logging.debug(
        f"Init query results:\
                  \nQuery_ok:\n\t{query_ok}\
                  \nquery_status: \n\t{query_status}\
                  \nstreams: \n\t{streams}"
    )

    if not query_ok:
        logging.debug("Attempting token refresh.")
        refresh_token(config_filepath, config)
        query_ok, query_status, streams = query_streams(config)

    # region logging
    debug_lines = [
        "Config file player settings:",
        f"\tPlayer: {config['PlayerBits']['player']}",
        f"\tArguments: {config['PlayerBits']['arguments']}",
        "Argparse player settings:",
        f"\tPlayer: {args.player}",
        f"\tArguments: {args.arguments}",
        f"Player setting: {player_config['player']}",
        f"Player arguments: {player_config['arguments']}",
        f"playerFlag: {player_config['playerFlag']}",
    ]
    logging.debug("\n".join(debug_lines))
    # endregion

    if query_ok:
        write_results(streams, player_config)
        if player_config["playerFlag"]:
            player_selection(player_config, streams)
    else:
        print(
            f"Error getting stream data. Response code: {query_status} \n \
              Please verify your values in the config file and try again."
        )


# endregion

# Added to enable debugging without having to make file changes.
if __name__ == "__main__":
    main()
