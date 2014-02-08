from config import *
from spotify import Link

import json

class JsonQueue:
    _done_starred = False
    _in_starred   = True
    _items        = None
    _position     = 0

    def add_artist_link(self, artist, source):
        """
        Add an artist link to the queue.
        """
        link = str(Link.from_artist(artist))

        if not self._items:
            self._items = { }

            with open('queue.json', 'r') as fp:
                self._items = json.load(fp)

        if not link in self._items:
            while not artist.is_loaded():
                time.sleep(0.1)

            print 'Adding %s' % artist.name()

            self._items[link] = {
                    'name':   artist.name(),
                    'link':   link,
                    'source': source,
                    }

            with open('queue.json', 'w') as fp:
                json.dump(self._items, fp, indent=2)

        return True

    def next_link(self):
        """
        Get the next link in the queue (as a string).
        """
        if not self._done_starred:
            self._done_starred = True
            return 'spotify:user:'+config_get('username')+':starred'
        else:
            # if we are asked for a link and we've given the starred link, we
            # are no longer in the 'starred' album
            self._in_starred = False

        retval = list(self._items)[self._position]
        self._position += 1

        return retval

    def is_downloaded(self, link):
        """
        Determine if a link has been downloaded.
        """
        found = False

        with open('downloaded', 'r') as fp:
            lines = fp.readlines()
            for line in lines:
                if str(link) in line:
                    found = True
                    break

        return found

    def mark_as_downloaded(self, link):
        if not self.is_downloaded(link):
            with open('downloaded', 'a') as fp:
                fp.write(str(link)+"\n")

    def is_starred_track(self):
        return self._in_starred
