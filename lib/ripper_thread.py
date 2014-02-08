from config import *

from lib.jukebox import \
        TrackNotAvailableException, \
        container_loaded

from lib.util import \
        AlbumType, \
        Util

from spotify import \
        AlbumBrowser, \
        ArtistBrowser, \
        Link

from threading import \
        Event, \
        Thread

import time

class RipperThread(Thread):
    _end_of_track = None
    _queue        = None
    _ripper       = None
    _util         = None

    def get_end_of_track(self):
        return self._end_of_track

    def __init__(self, ripper, queue):
        Thread.__init__(self)

        self._end_of_track = Event()
        self._queue        = queue
        self._ripper       = ripper
        self._util         = Util(self._queue)

    def run(self):
        # wait for container
        container_loaded.wait()
        container_loaded.clear()

        while True:
            link_string = self._queue.next_link()

            if link_string == '':
                break

            link = Link.from_string(link_string)

            if link.type() == Link.LINK_TRACK:
                track = link.as_track()
                itrack = iter([track])

            elif link.type() == Link.LINK_PLAYLIST \
                    or link_string == 'spotify:user:'+config_get('username')+':starred':
                print 'Loading playlist %s ...' % link_string

                playlist = link.as_playlist()

                while not playlist.is_loaded():
                    time.sleep(0.1)

                itrack = iter(playlist)

            elif link.type() == Link.LINK_ALBUM:
                print 'Processing album %s' % str(link)
                itrack = [ ]
                album = link.as_album()
                album_browser = AlbumBrowser(album)

                while not album_browser.is_loaded():
                    time.sleep(0.1)

                if album.type() == AlbumType.Compilation \
                        or album.artist().name().lower() == 'various artists' \
                        or 'the best of' in album.name().lower() \
                        or 'the very best of' in album.name().lower():
                    # print 'Skipping compilation %s' % album.name()
                    continue

                if album.is_available():
                    print 'Getting tracks for %s' % album.name()
                    for track in album_browser:
                        itrack.append(track)

            elif link.type() == Link.LINK_ARTIST:
                print "Processing artist %s ..." % str(link)

                artist         = link.as_artist()
                artist_browser = ArtistBrowser(artist, 'no_tracks')

                while not artist_browser.is_loaded():
                    time.sleep(0.1)

                print "Artist loaded"
                print(artist.name())

                similar_artists = artist_browser.similar_artists()

                for similar_artist in similar_artists:
                    self._queue.add_artist_link(similar_artist, 'similar')

                albums           = artist_browser.albums()
                processed_albums = [ ]
                itrack           = [ ]

                for album in albums:
                    if album.type() == AlbumType.Compilation \
                            or album.artist().name().lower() == 'various artists' \
                            or 'the best of' in album.name().lower() \
                            or 'the very best of' in album.name().lower():
                        # print 'Skipping compilation %s' % album.name()
                        continue

                    if album.is_available() and Link.from_album(album) \
                            not in processed_albums:
                        processed_albums.append(Link.from_album(album))
                        print 'Getting tracks for %s' % album.name()
                        album_browser = AlbumBrowser(album)

                        while not album_browser.is_loaded():
                            time.sleep(0.1)

                        for track in album_browser:
                            itrack.append(track)

            else:
                print "Unrecognised link"
                os._exit(2)
                return

            # ripping loop
            session = self._ripper.session

            for track in itrack:
                if self._util.is_known_not_available(Link.from_track(track)):
                    continue

                try:
                    self._ripper.load_track(track)

                    while not track.is_loaded():
                        time.sleep(0.1)

                    for track_artist in track.artists():
                        self._queue.add_artist_link(track_artist, 'track')

                    if self._ripper.rip_init(session, track):
                        self._ripper.play()
                        self._end_of_track.wait()
                        self._end_of_track.clear()
                        self._ripper.rip_terminate(session, track)
                        self._ripper.rip_id3(session, track)

                except TrackNotAvailableException:
                    print "Track not available (%s)" % track.name()
                    self._util.mark_as_not_available(Link.from_track(track))

        self._ripper.disconnect()
