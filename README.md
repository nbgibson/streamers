# streamers

A CLI tool inspired by [begs's](https://github.com/begs) [livestreamers](https://github.com/begs/livestreamers) script. Queries Twitch's API to see what followed channels, if any, are currently broadcasting. Can also open a given string in a selection of players if so desired.

## Ok, so what's the deal here?

Twitch doesn't provide a readily available method to pull down followed stream status via CLI so we need to set up a method to get at the data and display it in a easy to read fashion. This package performs that pretty well (though I'm not an impartial source), but setting up this data and so forth automatically is a bit beyond the current scope of the program and my personal scope of "things I'm willing to put up with"&trade;. So you're going to want to read the docs, though you're doing that already. Good for you.

## Installation

The application is now available in ~~pog~~ package form [via pip](https://pypi.org/project/streamers/)! Simply install via:

```bash
pip install streamers
```

## Package Requirements

- An existing Twitch account
- Some flavor of Python3
- The Python requests library: 2.26.0 or newer
- Streamlink: 5.3.0 or newer
- An Internet connection

## Execution

Once installed via pip, the package should be present on your system's PATH and can be called via:

```bash
streamers
```

If you recieve errors that the command is not known, please ensure that the install location (HINT: `pip list -v`) is included on your system's PATH. Please consult your preferred search engine on how to accomplish this if needed.

## So how do we go about getting the data to make this work?

1. Once installed, execute the package to generate a dummy config file: `~/.config/streamers/config` that should read as follows:

   ```ini
   [TwitchBits]
   userid = foo
   clientid = bar
   access_token = fizz
   refreshtoken = buzz
   clientsecret = fizzbuzz

   [PlayerBits]
   player=
   arguments=
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
   {
     "access_token": "[Some_Access_Token]",
     "expires_in": 14151,
     "refresh_token": "[Some_Refresh_Token]",
     "scope": ["user:read:follows"],
     "token_type": "bearer"
   }
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

9. Bask in a sense of self accomplishment; maybe watch a stream or something. Note that every few hours the existing token you have should expire and no longer work. If this happens the package should detect it, attempt to refresh it automatically, and prompt you to re-run it. If this does not work, please verify the values in the config file.

## Hey I'd like to, you know, *watch* these streams too. Preferbly without having to leave the CLI to do so.

Buddy, I've got just the thing for you. As of version 1.2, Streamers now can optionall start the stream of your choice in one of a number of players (IINA, MPV, Streamlink, and VLC) if so desired. Use the `-p/--player` flag to provide your choice and `-a/--arguments` to provide a finer grain of control to your selection. For those of you looking for more of a committment, you can also set these values in your confile file for automatic intake.

**NOTE:** If passing an argument/arguments starting with a dash (-), use the format `-a="--i-luv-streamers"` or you will encounter errors. Argparse, not me! :^)

### Wait a minute, Streamlink isn't a player.
Shut up.

### TODOs

- ~~Implement debugging/logging/ect~~ Accessable via the `-l/--logging` flag!
- ~~Investigate integration with [Streamlink](https://github.com/streamlink/streamlink)~~
- ~~Look into automated testing~~ Implemented by [cakebizzle](https://github.com/cakebizzle)
- Streamline onboarding
- Make output configurable
- ~~Investigate the viability of packaging~~
- ~~Terrible horrible godawful in CLI streams~~ Now possbile via MPV!

# Known issues
- Authentication tokens will expire over a given length of time, causing the application to throw an error. This can be resolved by repeating the onboarding process and inserting a new access token and refresh token (Steps 6 and 7). I'm working on refactoring the onboarding process to be a bit smoother and hope to be able to more gracefully handle this in the future.
- Config file schema changes are not backwards compatible and will requre updaing your files. Please see the documenation aboce for the expected format. Sorry for the trouble.
