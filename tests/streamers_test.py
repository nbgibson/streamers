import pytest
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple, Union

from streamers import streamers


@pytest.fixture
def config_path(tmp_path):
    d = tmp_path / "config_path"
    d.mkdir()
    return d


@pytest.fixture
def config_file(config_path):
    p = config_path / "test.cfg"
    p.write_text("""
    [TwitchBits]
    userid = AAAAA
    clientid = EEEEE
    access_token = IIIII
    refreshtoken = OOOOO
    clientsecret = UUUUU
    """)
    return p


@pytest.fixture
def empty_session_flags() -> Dict[str, Any]:
    session_flags = {
        "player": "",
        "playerFlag": False,
        "arguments": ""
    }
    return session_flags


@pytest.fixture
def mpv_session_flags(empty_session_flags) -> Dict[str, Any]:
    session_flags = empty_session_flags
    session_flags["player"] = "mpv"
    session_flags["playerFlag"] = "True"
    return session_flags


@pytest.fixture
def vlc_session_flags(empty_session_flags) -> Dict[str, Any]:
    session_flags = empty_session_flags
    session_flags["player"] = "vlc"
    session_flags["playerFlag"] = "True"
    return session_flags


def test_config_set_no_path(capsys):
    with pytest.raises(RuntimeError):
        result = streamers.config_set(None)


def test_config_set_no_file(config_path, capsys):
    with pytest.raises(SystemExit):
        result = streamers.config_set(config_path)


def test_config_set(config_file, capsys):
    result = streamers.config_set(config_file)

    captured = capsys.readouterr()

    stdout = captured.out

    assert "TwitchBits" in result
    assert "userid" in result["TwitchBits"]
    assert "AAAAA" in result["TwitchBits"]["userid"]

# @pytest.mark.skip("testing os calls is hard without mocking them.")


def test_start_player_no_player(capsys, empty_session_flags):
    dummy_stream = "dummystream"

    result = streamers.start_player(dummy_stream, empty_session_flags)
    captured = capsys.readouterr()
    assert result == False

    stdout = captured.out

    assert "is either not installed or on the system's PATH. Please verify that it is present and retry." in stdout

# @pytest.mark.skipif(shutil.which("mpv") == None, reason="mpv is not installed on the system")


@pytest.mark.skip(reason="Attempts to launch an unknown stream")
def test_start_player_mpv(capsys, mpv_session_flags):
    dummy_stream = "dummystream"

    result = streamers.start_player(dummy_stream, mpv_session_flags)
    captured = capsys.readouterr()
    assert result == True

    stdout = captured.out

    assert f"Starting {mpv_session_flags['player']} with command: {shutil.which('vlc')} {mpv_session_flags['arguments']} https://twitch.tv/{dummy_stream}" in stdout

# @pytest.mark.skipif(shutil.which("vlc") == None, reason="vlc is not installed on the system")


@pytest.mark.skip(reason="Attempts to launch an unknown stream")
def test_start_player_vlc(capsys, vlc_session_flags):
    dummy_stream = "dummystream"

    result = streamers.start_player(dummy_stream, vlc_session_flags)
    captured = capsys.readouterr()
    assert result == True

    stdout = captured.out

    assert f"Starting {vlc_session_flags['player']} with command: {shutil.which('vlc')} {vlc_session_flags['arguments']}" in stdout


def test_write_results_no_streamlink(capsys, empty_session_flags):

    dummy_streams = {
        "data": [
            {
                "user_name": "test",
                "game_name": "foo",
                "viewer_count": 69
            }
        ]
    }

    result = streamers.write_results(dummy_streams, empty_session_flags)
    captured = capsys.readouterr()
    assert result == True

    stdout = captured.out

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

    assert table_header in stdout

    stdout = stdout.replace(table_header, "").strip().split(" ")
    stdout = [std for std in stdout if std]

    assert len(stdout) == 3
    assert stdout[0] == "test"
    assert stdout[1] == "foo"
    assert stdout[2] == "69"


def test_write_results_with_streamlink(capsys, mpv_session_flags):

    dummy_streams = {
        "data": [
            {
                "user_name": "test",
                "game_name": "foo",
                "viewer_count": 69
            }
        ]
    }

    result = streamers.write_results(dummy_streams, mpv_session_flags)
    captured = capsys.readouterr()
    assert result == True

    stdout = captured.out

    table_header = (
        "INDEX   CHANNEL "
        + " " * 13
        + "GAME"
        + " " * 37
        + "VIEWERS"
        + " " * 8
        + "\n"
        + "-" * 80
    )

    assert table_header in stdout

    print(stdout)

    stdout = stdout.replace(table_header, "").strip().split(" ")
    stdout = [std for std in stdout if std]

    assert len(stdout) == 4
    assert stdout[1] == "test"
    assert stdout[2] == "foo"
    assert stdout[3] == '69'


def test_write_results_with_streamlink(capsys, vlc_session_flags):

    dummy_streams = {
        "data": [
            {
                "user_name": "test",
                "game_name": "foo",
                "viewer_count": 69
            }
        ]
    }

    result = streamers.write_results(dummy_streams, vlc_session_flags)
    captured = capsys.readouterr()
    assert result == True

    stdout = captured.out

    table_header = (
        "INDEX   CHANNEL "
        + " " * 13
        + "GAME"
        + " " * 37
        + "VIEWERS"
        + " " * 8
        + "\n"
        + "-" * 80
    )

    assert table_header in stdout

    print(stdout)

    stdout = stdout.replace(table_header, "").strip().split(" ")
    stdout = [std for std in stdout if std]

    assert len(stdout) == 4
    assert stdout[1] == "test"
    assert stdout[2] == "foo"
    assert stdout[3] == '69'
