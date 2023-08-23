# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Thomas Amland
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
from kodi_six import xbmc, xbmcvfs, xbmcaddon, xbmcplugin
from kodi_six.xbmcgui import Dialog, ListItem
from kodi_six.utils import py2_encode, py2_decode
import routing
try:
    from urllib import urlencode, quote_plus
except ImportError:
    from urllib.parse import urlencode, quote_plus
import json

plugin = routing.Plugin()
addon = xbmcaddon.Addon()

def get_play_count(current_path, filename):
    json_query = '{"jsonrpc": "2.0", "method": "Files.GetFileDetails", "params":{"file":%s, "media":"video", "properties":["playcount"]}, "id": 1}' % (json.dumps(current_path + filename))
    xbmc.log("[%s] query %s" %
            (addon.getAddonInfo('id'), json_query), xbmc.LOGDEBUG)
    json_response = xbmc.executeJSONRPC(json_query)
    xbmc.log("[%s] response '%s'" %
            (addon.getAddonInfo('id'), json_response), xbmc.LOGDEBUG)
    response = json.loads(json_response)
    return response['result']['filedetails'].get('playcount', 0)

@plugin.route("/")
def browse():
    args = plugin.args

    if 'path' not in args:
        # back navigation workaround: just silently fail and we'll
        # eventually end outside the plugin dir
        xbmcplugin.endOfDirectory(plugin.handle, succeeded=False)
        return

    current_path = args['path'][0]
    if not current_path.endswith('/'):
        current_path += '/'

    dirs = []
    files = []

    if xbmcvfs.exists(current_path):
        dirs, files = xbmcvfs.listdir(current_path)

    for name in dirs:
        li = ListItem(name)
        path = os.path.join(current_path, name)
        params = {
            b'path': path,
            b'title': args['title'][0],
        }
        if 'fanart' in args:
            li.setArt({'fanart': args['fanart'][0]})
            params.update({b'fanart': args['fanart'][0]})
        url = 'plugin://context.item.extras/?' + urlencode(params)
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, isFolder=True)

    for name in files:
        li = ListItem(name)
        playCount = get_play_count(current_path, name)
        if playCount:
            li.getVideoInfoTag().setPlaycount(playCount)
        if 'fanart' in args:
            li.setArt({'fanart': args['fanart'][0]})
        url = os.path.join(current_path, py2_decode(name))
        xbmcplugin.addDirectoryItem(plugin.handle, url, li, isFolder=False)

    xbmcplugin.addSortMethod(plugin.handle, xbmcplugin.SORT_METHOD_LABEL)
    xbmcplugin.endOfDirectory(plugin.handle)
    xbmcplugin.setContent(plugin.handle, 'videos')


@plugin.route("/youtube")
def youtube():
    query = plugin.args['q'][0]
    kb = xbmc.Keyboard(query, 'Search')
    kb.doModal()
    if kb.isConfirmed():
        edited_query = kb.getText()
        if edited_query:
            url = "plugin://plugin.video.youtube/kodion/search/query/?q=" + \
                  quote_plus(edited_query)
            xbmc.executebuiltin('Container.Update(\"%s\")' % url)


if __name__ == '__main__':
    plugin.run()
