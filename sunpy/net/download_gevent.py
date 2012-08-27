# -*- coding: utf-8 -*-
# Author: Florian Mayer <florian.mayer@bitsrc.org>

from __future__ import absolute_import

from gevent import monkey
monkey.patch_all()

import urllib2

from collections import deque

import gevent

from gevent.pool import Pool
import sunpy

from sunpy.net.download import default_name
from sunpy.util.util import buffered_write


class QueuePool(object):
    def __init__(self, size):
        self.waiting = deque()
        self.size = size
        self.running = set()

    def _spawn(self, function, *args, **kwargs):
        spawned = gevent.spawn(function, *args, **kwargs)
        spawned.link(self.refill)
        self.running.add(spawned)

    def spawn_queue(self, function, *args, **kwargs):
        if self.full():
            self.waiting.append((function, args, kwargs))
        else:
            self._spawn(function, *args, **kwargs)

    def refill(self, greenlet):
        self.running.remove(greenlet)
        while self.waiting and not self.full():
            function, args, kwargs = self.waiting.pop()
            self._spawn(function, *args, **kwargs)

    def full(self):
        return len(self.running) == self.size

    def joinall(self):
        while True:
            gevent.joinall(self.running)
            if not self.waiting:
                return

    def killall(self):
        self.waiting = deque()
        for greenlet in self.running:
            greenlet.kill()


class Downloader(object):
    def __init__(self, max_total=20):
        self.pool = QueuePool(max_total)
        self.buf = 9096
    
    def _download(self, url, path, callback, errback):
        sock = urllib2.urlopen(url)
        fullname = path(sock, url)
        
        try:
            fd = open(fullname, 'wb')
        except IOError, e:
            if errback is not None:
                return errback(e)
        buffered_write(sock, fd, self.buf)
        callback({'path': fullname})    

    def _default_callback(self, *args):
        """Default callback to execute on a successful download"""
        pass
        
    def _default_error_callback(self, e):
        """Default callback to execute on a failed download"""
        raise e

    def download(self, url, path=None, callback=None, errback=None):
        """Downloads a file at a specified URL.
        
        Parameters
        ----------
        url : string
            URL of file to download
        path : function, string
            Location to save file to. Can specify either a directory as a string
            or a function with signature: (path, url).
            Defaults to directory specified in sunpy configuration
        callback : function
            Function to call when download is successfully completed
        errback : function
            Function to call when download fails
            
        Returns
        -------
        out : None
        """
        # Create function to compute the filepath to download to if not set
        default_dir = sunpy.config.get("downloads", "download_dir")
        
        if path is None:
            path = partial(default_name, default_dir)
        elif isinstance(path, basestring):
            path = partial(default_name, path)
        
        # Use default callbacks if none were specified
        if callback is None:
            callback = self._default_callback
        if errback is None:
            errback = self._default_error_callback
        
        # Attempt to download file from URL
        self.pool.spawn_queue(self._download, url, path, callback, errback)

    def start(self):
        pass
    
    def stop(self):
        self.pool.killall()

    def run_sync(self, fun):
        fun()


if __name__ == '__main__':
    import tempfile
    from functools import partial

    def wait_for(n, callback): #pylint: disable=W0613
        items = []
        def _fun(handler):
            items.append(handler)
            if len(items) == 4:
                callback(items)
        return _fun
    
    
    tmp = tempfile.mkdtemp()
    print tmp
    path_fun = partial(default_name, tmp)
    
    dw = Downloader(2)
    
    on_finish = wait_for(4, lambda _: dw.stop())
    dw.download('http://google.at', path_fun, on_finish)
    dw.download('http://google.de', path_fun, on_finish)
    dw.download('https://bitsrc.org', path_fun, on_finish)
    dw.download('ftp://speedtest.inode.at/speedtest-100mb', path_fun, on_finish)
    
    # print dw.conns
    print dw.pool.running
    dw.pool.joinall()
    dw.start()
