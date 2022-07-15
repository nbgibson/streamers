# streamers

A CLI tool inspired by [begs's](https://github.com/begs) [livestreamers](https://github.com/begs/livestreamers) script. Queries Twitch's API to see what followed channels, if any, are currently broadcasting.

## Ok, so what's the deal here?

Twitch doesn't provide a readily available method to pull down followed stream status via CLI so we need to set up a method to get at the data and display it in a easy to read fashion. This script performs that pretty well (though I'm not an impartial source), but setting up this data and so forth automatically is a bit beyond the current scope of the program and my personal scope of "things I'm willing to put up with"&trade;. So you're going to want to read the docs, though you're doing that already. Good for you.

## Installation

Simply clone down or save the streamers.py script to your system, preferably in a location on your System Path. If not already present, install the requests library via the command below or via `pip install -r requirements.txt`.

## Script Requirements

- An existing Twitch account
- Some flavor of Python3
- The Python requests library: `pip install --user requests` || `pip install -r requirements.txt`
- An Internet connection

## Execution

Assuming Python is installed on your system (it probably is) simply make the script executable via `chmod a+x streamers.py` if needed and execute it. The script should hook into your system's python install automatically. Windows folks: I'm still working on a better way to go about this, but you currently have to run `python3 streamers.py` from within cmd/powershell. If you've got ideas I'm happy to hear them.

## So how do we go about making this work?

1. Download the script, put it in some location, and execute it to generate a dummy config file: `~/.config/streamers/config` that should read as follows:

    ```ini
    [TwitchBits]
    userid = foo
    clientid = bar
    access_token = fizz
    refreshtoken = buzz
    clientsecret = fizzbuzz

    [StreamLinkBits]
    enabled = false
    ```

2. Head on over to the [Twitch developer console](https://dev.twitch.tv/console) and make an account ([docs](https://dev.twitch.tv/docs/authentication/register-app)) if you do not already have one.

3. Make an App and register it ("Register Your Application"):
    - Name: Can be anything you please, is not critical for our workflow.
    - OAuth Redirect URLs: Again, can be anything you please for this workflow, but the documentation assumes you have used `http://localhost:3000`
    - Category: Arbitrary unless you're attempting to do this at a large scape. 'Other' and a description of what you're doing should be fine.

4. Select 'Manage' for your newly created app and make note of the 'Client ID'. As you may have guessed this is what you want for the `clientid` value in the config file.

5. From the same screen select 'New Secret' in the 'Client Secret' section near the bottom of the page and approve the generation of a new secret. Copy and save this somewhere as it will not be displayed once you leave the page. Insert this value for the `clientsecret` portion of the config file. Be advised that if you regenerate the secret it will wipe out old secrets so be sure to keep things synced up.

6. Now we need to generate a code from your Twitch user account that says that the application you created has access to your data and then use that to generate a token that will be used with the script's API calls to do so.

    - Enter the following URL into a browser window of your choosing, subbing out '[Your_Client_ID_Goes_Here]' for the client ID value you got in step 4:
    `https://id.twitch.tv/oauth2/authorize?response_type=code&client_id=[Your_Client_ID_Goes_Here]&redirect_uri=http://localhost:3000&scope=user%3Aread%3Afollows`
    - You will be prompted to provide access to the application to see who your Twitch account follows, approve the prompt as this won't work otherwise.
    - After approval you will be dumped to an empty/broken page, note the URL displayed in your address bar. It will contain something similar to the following: `http://localhost:3000/?code=[Some_30ish_Character_Code]&scope=user%3Aread%3Afollows` Copy that code down as we will need it in the next step.

7. We'll now take that code and send it back to Twitch to get an authorization and refresh token back so we can actually go about our business. Open up a terminal window (or Powershell/cmd/whatever) and enter the following command:

    ```bash
    curl -X POST 'https://id.twitch.tv/oauth2/token' -d 'client_id=[Your_Client_ID]&client_secret=[Your_Client_Secret]&code=[The_Code_From_Step_6]&grant_type=authorization_code&redirect_uri=http://localhost:3000'
    ```

    You should get back some JSON that looks something like the following:

    ```json
    {"access_token":"[Some_Access_Token]","expires_in":14151,"refresh_token":"[Some_Refresh_Token]","scope":["user:read:follows"],"token_type":"bearer"}
    ```

    Take the values for `access_token` and `refresh_token` and insert them into your config file for `access_token` and `refreshtoken` accordingly. You should be all set.

8. Execute the script and you should get back a table similar to the following:

    ```bash
    CHANNEL              GAME                                     VIEWERS
    --------------------------------------------------------------------------------
    GiantBomb            Talk Shows & Podcasts                    755
    SaltyBet             Retro                                    379
    giantbomb8                                                    97
    ```

9. Bask in a sense of self accomplishment; maybe watch a stream or something. Note that every few hours the existing token you have should expire and no longer work. If this happens the script should detect it, attempt to refresh it automatically, and prompt you to re-run it. If this does not work, please verify the values in the config file.

## Hey, I'd like to have this hook into [Streamlink](https://github.com/streamlink/streamlink)

Buddy, I've got just the thing for you. If streamlink is installed on your system('s PATH) and you pass the `-s` flag to the script (or set enabled to 'True' in the [StreamLinkBits] section of the config) then you will be prompted to select a stream to watch that will then be called in Streamlink. At this time that just amounts to `streamlink https://twitch.tv/[streamer]` so be sure to set up a [config file](https://streamlink.github.io/cli/config.html).

### TODOs

- Implement debugging/logging/ect
- ~~Investigate integration with [Streamlink](https://github.com/streamlink/streamlink)~~
- Look into automated testing
- Investigate the viability of packaging
