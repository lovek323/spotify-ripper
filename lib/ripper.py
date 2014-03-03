from clint.textui import colored, indent, puts, progress
from jukebox import Jukebox, Link
from lib.json_queue import JsonQueue
from lib.ripper_thread import RipperThread
from lib.util import Util
from subprocess import PIPE, Popen

import os
import sys
import time

class Ripper(Jukebox):
    _all_processes = [ ]
    _dot_count     = 0
    _downloaded    = 0.0
    _duration      = 0
    _end_of_track  = None
    _pipe          = None
    _json_queue    = None
    _ripper_thread = None
    _ripping       = False
    _util          = None

    def __init__(self, *a, **kw):
        Jukebox.__init__(self, *a, **kw)

        self._json_queue = JsonQueue()
        self._util       = Util(self._json_queue)

        self._ripper_thread = RipperThread(self, self._json_queue)
        self._end_of_track = self._ripper_thread.get_end_of_track()
        self.set_ui_thread(self._ripper_thread)

        self.session.set_preferred_bitrate(1) # 320 kbps (ostensibly)

    def music_delivery_safe(self, \
            session, \
            frames, \
            frame_size, \
            num_frames, \
            sample_type, \
            sample_rate, \
            channels):
        self.rip(
                session,
                frames,
                frame_size,
                num_frames,
                sample_type,
                sample_rate,
                channels)
        return num_frames

    def end_of_track(self, session):
        Jukebox.end_of_track(self, session)
        self._end_of_track.set()

    def rip_init(self, session, track):
        mp3_path = self._util.get_mp3_path(track, escaped = False)

        print ''
        print colored.yellow(str(Link.from_track(track)))

        with indent(3, quote = colored.white(' > ')):
            if self._json_queue.is_downloaded(Link.from_track(track)) \
                    or os.path.isfile(mp3_path):
                try:
                    puts('Skipping %s' % mp3_path)
                except UnicodeEncodeError:
                    # Non-ASCII characters
                    sys.stdout.write(' > Skipping %s\n' % mp3_path)
                return False
            else:
                try:
                    puts('Downloading %s' % mp3_path)
                except UnicodeEncodeError:
                    # Non-ASCII characters
                    sys.stdout.write(' > Downloading %s\n' % mp3_path)

            album   = track.album().name()
            title   = track.name()
            number  = str(track.index()).zfill(2)
            disc    = str(track.disc()).zfill(2)
            year    = track.album().year()
            artists = ''

            for artist in track.artists():
                while not artist.is_loaded():
                    time.sleep(0.1)

                artists += artist.name()+' / '

            artists = artists.strip().rstrip('/').rstrip()

            puts('Track URI:    %s'        % Link.from_track(track))

            try:
                puts('Album:        %s (%i)'   % (album, year))
            except UnicodeEncodeError:
                sys.stdout.write(' > Album:        %s (%i)\n' % (album, year))

            try:
                puts('Artist(s):    %s'        % artists)
            except UnicodeEncodeError:
                sys.stdout.write(' > Artist(s):    %s\n' % artists)

            puts('Album artist: %s'        % track.album().artist().name())

            try:
                puts('Track:        %s-%s. %s' % (disc, number, title))
            except UnicodeEncodeError:
                sys.stdout.write(' > Track:        %s-%s. %s \n' \
                        % (disc, number, title))

        command = 'lame -b 320 -h -r --silent - temp.mp3'
        p = Popen(command, stdin=PIPE, shell=True)
        self._all_processes.append(p)

        self._pipe       = p.stdin
        self._ripping    = True
        self._dotCount   = 0
        self._downloaded = 0.0
        self._duration   = track.duration()

        return True

    def rip_terminate(self, session, track):
        if self._pipe is not None:
            self._pipe.close()
        self._ripping = False

    def rip(self,
            session,     # the current session
            frames,      # the audio data
            frame_size,  # bytes per frame
            num_frames,  # number of frames in this delivery
            sample_type, # currently this is always 0, which means 16-bit
                         # signed native endian integer samples
            sample_rate, # audio sample rate, in samples per second
            channels):   # number of audio channels, currently 1 or 2

        self._downloaded += float(frame_size) * float(num_frames)

        if self._ripping:
            # 320 kilobits per second
            # 40 kilobytes per second
            # duration in milliseconds
            # 40 bytes per millisecond

            total_bytes = float(self._duration) * 40.0
            # 100 = 4.41 (don't ask me why)
            progress_perc = self._downloaded / total_bytes
            progress_perc = progress_perc * (100.0 / 4.41)
            progress.bar(range(100))
            sys.stdout.write('\r > Progress:     %.2f%%' % progress_perc)

            try:
                self._pipe.write(frames);
            except IOError:
                os.kill(os.getpid(), 9)

    def rip_id3(self, session, track): # write ID3 data
        mp3_path = self._util.get_mp3_path(track)

        if self._json_queue.is_starred_track():
            album = 'Spotify Starred'
        else:
            album = track.album().name()

        disc       = track.disc()
        number     = track.index()
        title      = track.name()
        year       = track.album().year()
        artist     = track.album().artist().name()
        performers = ''

        for performer in track.artists():
            performers += performer.name()+', '

        performers = performers.strip().rstrip(',')

        if not self._json_queue.is_starred_track():
            # download cover
            image = session.image_create(track.album().cover())

            while not image.is_loaded():
                time.sleep(0.1)

            with open('cover.jpg', 'wb') as fp:
                fp.write(image.data())

        # write id3 data
        cmd = 'eyeD3'+\
              ' --title '   +self._util.shellescape(title)+\
              ' --artist '  +self._util.shellescape(performers)+\
              ' --album '   +self._util.shellescape(album)

        if not self._json_queue.is_starred_track():
            cmd = cmd\
                    +' --track '          +str(number) \
                    +' --disc-num '       +str(disc) \
                    +' --release-year '   +str(year) \
                    +' --recording-date ' +str(year) \
                    +' --add-image cover.jpg:FRONT_COVER' \
                    +' --text-frame TPE2:'+self._util.shellescape(artist)
        else:
            cmd = cmd+ \
                    ' --text-frame TPE2:' \
                    +self._util.shellescape('Various Artists')

        cmd = cmd+' temp.mp3 &>/dev/null'
        print ''

        with indent(3, quote = colored.cyan(' # ')):
            try:
                puts('Executing %s' % cmd)
            except UnicodeEncodeError:
                sys.stdout.write(' # Executing %s\n' % cmd)

            self._util.shell(cmd)

            try:
                puts('Moving %s to %s' % ('temp.mp3', mp3_path))
            except UnicodeEncodeError:
                sys.stdout.write(' # Moving %s to %s\n' \
                        % ('temp.mp3', mp3_path))

        # move mp3 to final directory
        cmd = 'mv temp.mp3 %s' % mp3_path
        self._util.shell(cmd)

        # delete cover
        if not self._json_queue.is_starred_track():
            self._util.shell("rm -f cover.jpg")

        self._json_queue.mark_as_downloaded(Link.from_track(track))
