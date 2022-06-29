# collabot
`collabot` is a bot that retrieves artists from spotify playlists and their related artists sections, and generates random artists associations that get tweeted to the associated account.

See it in action [here](https://twitter.com/collabot1)

Installation
============

```
git clone https://github.com/axelccccc/collabot.git
```

It is strongly advised to install and use the program in a separate environment (venv, conda, etc.).
Once in your environment : 
```
pip install -r requirements.txt
```

You should then fill the twitter and spotify API keys with yours in the `main.py` file, in the `SETTINGS` section.

Usage
=====

Use the `-h` or `--help` option to see the full list of available options.

## Playlist IDs

The ID of a Spotify playlist to be fed to the `-p` / `--playlist` option is the last string of characters at the end of a Spotify playlist URL.

```
https://open.spotify.com/playlist/PLAYLIST_ID
```

Tools
=====

`run-bot.sh` is a script I feed to `chrontab` to run the bot periodically.
`select_artists.py` allows to keep or remove artists one by one in an artist list quickly with left and right arrow keys.