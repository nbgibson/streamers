#!/usr/bin/env python 
#regions imports
import configparser
import requests
from pathlib import Path
#endregion

#region functions
def config_set(configDir, configPath): #Check if the config file is present, and if not create it with dummy values
    if not (configDir.is_dir()):
        print("Creating config dir at: " + str(configDir))
        Path.mkdir(configDir)
    if not (configPath.is_file()):
        print("Config file not found. Creating dummy file at: " + str(configPath))
        config = configparser.ConfigParser()
        Path(configPath).touch()
        config['TwitchBits'] = {'userID': 'foo', 'clientID': 'bar', 'access_token': 'fizz', 'refreshToken': 'buzz', 'clientSecret': 'fizzbuzz'}
        with open(configPath, 'w') as configfile:
            config.write(configfile)
        print("Please refer to the README.md to get guidance on how to generate the needed values for the config file.")
    else:
        #Populate vars
        config = configparser.RawConfigParser()
        config.read(configPath)
    return config
        
def query_streams(config):
    headers = { 'Authorization': 'Bearer ' + config['TwitchBits']['access_token'], 'Client-Id': config['TwitchBits']['clientID'] }
    data = { 'user_id': config['TwitchBits']['userID'] }
    r = requests.get('https://api.twitch.tv/helix/streams/followed', params=data, headers=headers)
    return r

def refresh_token(configPath, config):
    print("Renewing Token...")
    headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
    data = 'grant_type=refresh_token&refresh_token=' + config['TwitchBits']['refreshToken'] + '&client_id=' + config['TwitchBits']['clientID'] + '&client_secret=' + config['TwitchBits']['clientSecret']
    r = requests.post('https://id.twitch.tv/oauth2/token', headers=headers, data=data)
    config.set('TwitchBits', 'access_token', r.json()["access_token"])
    with open(configPath, 'w') as configfile:
            config.write(configfile)

def write_results(streams):
    print ("\nCHANNEL " + ' '*13 + "GAME" + ' '*37 + "VIEWERS" + ' '*8 + "\n" + '-'*80)
    for stream in streams.json()["data"]:
         print ("{} {} {}".format(stream['user_name'].ljust(20), stream['game_name'].ljust(40), str(stream['viewer_count']).ljust(8)))
#endregion

#region main
configDir = Path('~/.config/livestreamcheck').expanduser()
configFile = Path('~/.config/livestreamcheck/config').expanduser()



#Verify config dir is present and create one if it is not. TODO: Walk through values needed in README.md
config = config_set(configDir, configFile)

#Deadman's switch
if config['TwitchBits']['userID'] == "foo":
    print("Quitting program. Please populate config file.")
    quit()

streams = query_streams(config)
if streams.ok:    
    write_results(streams)
else:
    print("Error getting stream data. Response code: " + str(streams.status_code))
    refresh_token(configFile, config)
    print("Attempting token refresh, please try again")
#endregion
