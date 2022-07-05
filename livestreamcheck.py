#!/home/nate/.local/bin/livestreamcheck/venv/bin/python3
#regions imports
import json
import requests
from pathlib import Path
#endregion

#region functions
def check_config(configPath): #Check if the config dir is present, and if not create it and a config file
    if not (configPath.is_dir()):
        configPath.mkdir()
        Path(configPath / "userID").touch()
        Path(configPath / "clientID").touch()
        Path(configPath / "token").touch()
        Path(configPath / "refreshToken").touch()
        Path(configPath / "clientSecret").touch()
        print("Please populate the files in '~/.config/livestreamcheck' with their proper values.")

def query_streams(userID, clientID, token):
    headers = { 'Authorization': 'Bearer ' + token, 'Client-Id': clientID }
    data = { 'user_id': userID }

    r = requests.get('https://api.twitch.tv/helix/streams/followed', params=data, headers=headers)
    return r

def refresh_token(refreshToken, clientID, clientSecret, configPath):
    print("Renewing Token...")
    headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
    data = 'grant_type=refresh_token&refresh_token=' + refreshToken + '&client_id=' + clientID + '&client_secret=' + clientSecret
    r = requests.post('https://id.twitch.tv/oauth2/token', headers=headers, data=data)
    
    newToken_json_string = r.json()
    newToken_json_dump = json.dumps(newToken_json_string)
    newToken_json_object = json.loads(newToken_json_dump)
    newToken = newToken_json_object["access_token"]
    Path(configPath / "token").write_text(newToken)

def write_results(streams):
    streamlist = json.loads(streams.text)
    s = streamlist['data']
    print ("\nCHANNEL " + ' '*13 + "GAME" + ' '*37 + "VIEWERS" + ' '*8 + "\n" + '-'*80)
    for stream in s:
         print ("{} {} {}".format(stream['user_name'].ljust(20), stream['game_name'].ljust(40), str(stream['viewer_count']).ljust(8)))
#endregion

#region varibles
configPath = Path('~/.config/livestreamcheck').expanduser()
userID = Path(configPath / "userID").read_text().strip()
clientID = Path(configPath / "clientID").read_text().strip()
token = Path(configPath / "token").read_text().strip()
refreshToken = Path(configPath / "refreshToken").read_text().strip()
clientSecret = Path(configPath / "clientSecret").read_text().strip()
#endregion

#region dostuff

#Verify config dir is present and create one if it is not. TODO: Walk through values needed in README.md
check_config(configPath)

#Use data pulled from config files to query Twitch API. Returns JSON and a status regardless of validity.
streams = query_streams(userID, clientID, token)

if streams.ok:    
    write_results(streams)
else:
    print("Error getting stream data. Response code: " + str(streams.status_code))
    refresh_token(refreshToken, clientID, clientSecret, configPath)
    print("Attempting token refresh, please try again")
#endregion
