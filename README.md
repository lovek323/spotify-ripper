# About

Create mp3s from spotify songs.

* Downloads songs on your `Starred` playlist
* Downloads songs from artists on your `Starred` playlists
* Downloads songs from artists similar to artists on your `Starred` playlist
* (And so on, downloading artists similar to those similar to those on your
  `Starred` playlist)

I have tested this on Mac OS X 10.9 with the default Python install. It works.
YMMV.


# Getting started

* Get a spotify app key and save it to `spotify_appkey.key`
* [Install libspotify](https://developer.spotify.com/technologies/libspotify/#libspotify-downloads)
* Add your credentials to `config.json`
* Add the destination directory to `config.json`
* Create an empty `queue.json`
* Run `virtualenv env` (if you don't have virtualenv installed, install it)
* Run `source env/bin/activate`
* Run `pip -r requirements.txt --allow-unverified PyAudio --allow-unverified
  eyeD3`
* Run `./run.py`

## Example `config.json`

```json
{
  "mp3_path": "/Volumes/Music",
  "username": "me",
  "password": "password"
}
```

## Example `queue.json`

```json
{ }
```


# TODO

* Add `verbose` mode
* Add option to allow compilations to be downloaded
* Deal with `libspotify` failures more gracefully
* Allow ordering of queue.json
* Document more things
* Make a better config reader
* Create `queue.json` if it doesn't exist


# Screenshot

![screenshot, yeah!](https://raw.github.com/lovek323/spotify-ripper/master/screen.png)
