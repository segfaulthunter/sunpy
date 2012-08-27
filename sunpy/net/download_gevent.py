# -*- coding: utf-8 -*-
# Author: Florian Mayer <florian.mayer@bitsrc.org>

from __future__ import absolute_import

import urllib2

import gevent

from gevent.pool import Pool
from gevent import monkey

import sunpy
from sunpy.util.util import buffered_write

monkey.patch_all()

class Downloader(object):
    def __init__(self, max_total=20):
        self.pool = Pool(max_total)
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
        
        print path

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
        self.pool.spawn(self._download, url, path, callback, errback)

    def start(self):
        pass
    
    def stop(self):
        pass

    def run_sync(self, fun):
        fun()
