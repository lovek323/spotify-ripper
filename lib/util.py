from config import *
from subprocess import call

import os
import sys

class Util:
    _queue = None

    def __init__(self, queue):
        self._queue = queue

    def printstr(self, str): # print without newline
        sys.stdout.write(str)
        sys.stdout.flush()

    def shell(self, cmdline): # execute shell commands (unicode support)
        call(cmdline, shell=True)

    def get_mp3_path(self, track, escaped = True):
        _mp3_path = config_get('mp3_path')

        if self._queue.is_starred_track():
            artist   = track.artists()[0].name()
            _mp3_path = _mp3_path+'/'+self.shellreplace('Spotify Starred')
            _mp3_path = _mp3_path+'/'+self.shellreplace(artist)
        else:
            artist   = track.album().artist().name()
            album    = track.album().name()
            year     = str(track.album().year())
            _mp3_path = _mp3_path+'/'+self.shellreplace(artist)
            _mp3_path = _mp3_path+'/'+self.shellreplace(album)
            _mp3_path = _mp3_path+' '+self.shellreplace('('+year+')')

        if not os.path.exists(_mp3_path):
            os.makedirs(_mp3_path)

        if not self._queue.is_starred_track():
            number = str(track.index()).zfill(2)
            disc = str(track.disc()).zfill(2)

            _mp3_path = _mp3_path+'/'+self.shellreplace(disc)+'-' \
                    +self.shellreplace(number)+'. '
        else:
            _mp3_path = _mp3_path+'/'

        _mp3_path = _mp3_path+self.shellreplace(track.name())
        _mp3_path = _mp3_path+".mp3"

        if escaped:
            return self.shellescape(_mp3_path)

        return _mp3_path

    def shellreplace(self, s):
        return s \
            .replace('!', '_') \
            .replace('/', '_') \
            .replace(':', '_')

    def shellescape(self, s):
        return s \
            .replace('"', '\\"') \
            .replace(' ', '\\ ') \
            .replace('\'', '\\\'') \
            .replace(';', '\\;') \
            .replace('(', '\\(') \
            .replace(')', '\\)') \
            .replace('[', '\\[') \
            .replace(']', '\\]') \
            .replace('&', '\\&') \
            .replace('#', '\\#')

    def is_known_not_available(self, link):
        f = open('not_available', 'r')
        lines = f.readlines()
        f.close()
        found = False
        for line in lines:
            if str(link) in line:
                found = True
                break
        return found

    def mark_as_not_available(self, link):
        if not self.is_known_not_available(link):
            f = open('not_available', 'a')
            f.write(str(link)+"\n")
            f.close()

class AlbumType:
    Album = 0
    Single = 1
    Compilation = 2
    Unknown = 3
