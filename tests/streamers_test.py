import pytest
from pathlib import Path
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

def test_config_set_no_path(tmp_path, capsys):
    with pytest.raises(AttributeError):
        result = streamers.config_set(None, None)

@pytest.mark.xfail(reason="None value is unhandled!")
def test_config_set_no_file(config_path, capsys):
    result = streamers.config_set(config_path, None)

def test_config_set(config_path, config_file, capsys):
    result = streamers.config_set(config_path, config_file)
    
    captured = capsys.readouterr()

    stdout = captured.out

    assert "TwitchBits" in result
    assert "userid" in result["TwitchBits"]
    assert "AAAAA" in result["TwitchBits"]["userid"]

@pytest.mark.skip("testing os calls is hard without mocking them.")
def test_stream_link(capsys):
    dummy_streams = {
        "data": [
            {"user_name": "test"}
        ]
    }

    streamers.stream_link(dummy_streams, "echo")

def test_write_results_no_streamlink(capsys):
    
    dummy_streams = {
        "data": [
            {
                "user_name": "test",
                "game_name": "foo",
                "viewer_count": 69
            }
        ]
    }

    streamers.write_results(dummy_streams, False)
    captured = capsys.readouterr()

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



def test_write_results_with_streamlink(capsys):
    
    dummy_streams = {
        "data": [
            {
                "user_name": "test",
                "game_name": "foo",
                "viewer_count": 69
            }
        ]
    }

    streamers.write_results(dummy_streams, True)
    captured = capsys.readouterr()

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
