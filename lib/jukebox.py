import cmd
import logging
import os
import threading
import time

from spotify import ArtistBrowser, Link, ToplistBrowser, SpotifyError
from spotify.audiosink import import_audio_sink
from spotify.manager import (
    SpotifySessionManager, SpotifyPlaylistManager, SpotifyContainerManager)

AudioSink = import_audio_sink()
container_loaded = threading.Event()

class TrackNotAvailableException(Exception):
    pass

class JukeboxPlaylistManager(SpotifyPlaylistManager):
    def tracks_added(self, p, t, i, u):
        print 'Tracks added to playlist %s' % p.name()

    def tracks_moved(self, p, t, i, u):
        print 'Tracks moved in playlist %s' % p.name()

    def tracks_removed(self, p, t, u):
        print 'Tracks removed from playlist %s' % p.name()

    def playlist_renamed(self, p, u):
        print 'Playlist renamed to %s' % p.name()


class JukeboxContainerManager(SpotifyContainerManager):
    def container_loaded(self, c, u):
        container_loaded.set()

    def playlist_added(self, c, p, i, u):
        print 'Container: playlist "%s" added.' % p.name()

    def playlist_moved(self, c, p, oi, ni, u):
        print 'Container: playlist "%s" moved.' % p.name()

    def playlist_removed(self, c, p, i, u):
        print 'Container: playlist "%s" removed.' % p.name()

class Jukebox(SpotifySessionManager):
    _ui = None

    queued = False
    playlist = 2
    track = 0
    appkey_file = os.path.join(os.path.dirname(__file__), '../spotify_appkey.key')

    def __init__(self, *a, **kw):
        SpotifySessionManager.__init__(self, *a, **kw)
        self.audio = AudioSink(backend=self)
        self.ctr = None
        self.playing = False
        self._queue = []
        self.playlist_manager = JukeboxPlaylistManager()
        self.container_manager = JukeboxContainerManager()
        self.track_playing = None
        print "Logging in, please wait..."

    def set_ui_thread(self, ui):
        self._ui = ui

    def new_track_playing(self, track):
        self.track_playing = track

    def logged_in(self, session, error):
        if error:
            print error
            return
        print "Logged in!"
        self.ctr = session.playlist_container()
        self.container_manager.watch(self.ctr)
        self.starred = session.starred()
        if not self._ui.is_alive():
            self._ui.daemon = True
            self._ui.start()

    def logged_out(self, session):
        print "Logged out!"

    def load_track(self, track):
        # print u"Loading track..."
        while not track.is_loaded():
            time.sleep(0.1)
        if track.is_autolinked():  # if linked, load the target track instead
            # print "Autolinked track, loading the linked-to track"
            return self.load_track(track.playable())
        if track.availability() != 1:
            raise TrackNotAvailableException()
        if self.playing:
            self.stop()
        self.new_track_playing(track)
        self.session.load(track)
        # print "Loaded track: %s" % track.name()

    def load(self, playlist, track):
        if self.playing:
            self.stop()
        if 0 <= playlist < len(self.ctr):
            pl = self.ctr[playlist]
        elif playlist == len(self.ctr):
            pl = self.starred
        spot_track = pl[track]
        self.new_track_playing(spot_track)
        self.session.load(spot_track)
        print "Loading %s from %s" % (spot_track.name(), pl.name())

    def load_playlist(self, playlist):
        if self.playing:
            self.stop()
        if 0 <= playlist < len(self.ctr):
            pl = self.ctr[playlist]
        elif playlist == len(self.ctr):
            pl = self.starred
        print "Loading playlist %s" % pl.name()
        if len(pl):
            print "Loading %s from %s" % (pl[0].name(), pl.name())
            self.new_track_playing(pl[0])
            self.session.load(pl[0])
        for i, track in enumerate(pl):
            if i == 0:
                continue
            self._queue.append((playlist, i))

    def queue(self, playlist, track):
        if self.playing:
            self._queue.append((playlist, track))
        else:
            print 'Loading %s', track.name()
            self.load(playlist, track)
            self.play()

    def play(self):
        self.audio.start()
        self.session.play(1)
        self.playing = True

    def pause(self):
        self.session.play(0)
        self.playing = False
        self.audio.pause()

    def stop(self):
        self.session.play(0)
        self.playing = False
        self.audio.stop()

    def music_delivery_safe(self, *args, **kwargs):
        return self.audio.music_delivery(*args, **kwargs)

    def next(self):
        self.stop()
        if self._queue:
            t = self._queue.pop(0)
            self.load(*t)
            self.play()
        else:
            self.stop()

    def end_of_track(self, sess):
        self.audio.end_of_track()

    def search(self, *args, **kwargs):
        self.session.search(*args, **kwargs)

    def browse(self, link, callback):
        if link.type() == link.LINK_ALBUM:
            browser = self.session.browse_album(link.as_album(), callback)
            while not browser.is_loaded():
                time.sleep(0.1)
            for track in browser:
                print track.name()
        if link.type() == link.LINK_ARTIST:
            browser = ArtistBrowser(link.as_artist())
            while not browser.is_loaded():
                time.sleep(0.1)
            for album in browser:
                print album.name()

    def watch(self, p, unwatch=False):
        if not unwatch:
            print "Watching playlist: %s" % p.name()
            self.playlist_manager.watch(p)
        else:
            print "Unatching playlist: %s" % p.name()
            self.playlist_manager.unwatch(p)

    def toplist(self, tl_type, tl_region):
        print repr(tl_type)
        print repr(tl_region)

        def callback(tb, ud):
            for i in xrange(len(tb)):
                print '%3d: %s' % (i+1, tb[i].name())

        ToplistBrowser(tl_type, tl_region, callback)

    def shell(self):
        import code
        shell = code.InteractiveConsole(globals())
        shell.interact()

# logging.basicConfig(level=logging.DEBUG)

