'''
    Furk.net player for XBMC
    Copyright (C) 2010 Gpun Yog

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''



import sys
import xbmc, xbmcaddon, xbmcgui, xbmcplugin
import urllib, urllib2
import re
import datetime
import math

# quircks for old xbmc
try:
  import json
  from urlparse import parse_qs
except: 
  # pre-frodo and python 2.4
  import simplejson as json
  from cgi import parse_qs

# Plugin constants
__settings__ = xbmcaddon.Addon(id='plugin.video.furk')
__plugin__ = 'Furk.net'
__author__ = 'Gpun Yog'
__url__ = 'https://www.furk.net/t/xbmc'
__version__ = '1.0.12'
print "[PLUGIN] '%s: version %s' initialized! argv=%s" % (__plugin__, __version__, sys.argv)

API_URL = "https://api.furk.net/api/"

pluginhandle = None
try:
    pluginhandle = int( sys.argv[ 1 ] )
except:
    pluginhandle = ""

xbmcplugin.setContent(pluginhandle, 'movies')
# based on whatthefurk plugin code
class FurkAPI(object):
    def __init__(self, api_key=''):
        self.api_key = api_key
        
    def metasearch(self, params):
        params['type'] = 'video'
        params['filter'] = 'cached'
        resp = self._call('plugins/metasearch', params)
        if resp.has_key('files'):
            return resp['files']
        else:
            return None

    def unlink(self, params):
        resp = self._call('file/unlink', params)
        return resp

    def account_info(self, params={}):
        resp = self._call('account/info', params)
        return resp

    def file_get(self, params={}):
        params['type'] = 'video'
        resp = self._call('file/get', params)
        files = resp['files']
        return files
        
    def login(self, login, pwd):
        resp = self._call('login/login', {"login": login, "pwd": pwd})
        if(resp):
            self.api_key = resp['api_key']
            return self.api_key
        else:
            return False

    def _call(self, cmd, params):
        url = "%s%s" % (API_URL, cmd)
        body = self._fetch(url, params)
        
        data = json.loads(body)
        if data['status'] != 'ok':
            xbmcgui.Dialog().ok('Error', data['error'])
            return None
        return data

    def _fetch(self, url, params):
        if self.api_key:
            params['api_key'] = self.api_key
        params['pretty'] = 1
        paramsenc = urllib.urlencode(params)
        req = urllib2.Request(url, paramsenc)
        opener = urllib2.build_opener()
        response = opener.open(req)

        body = response.read()
        response.close()
        return body


def switch_user_items():
    name = 'Switch to another account (current login: %s)' % (__settings__.getSetting('login'))
    icon_img =  os.path.dirname(__file__) + '/switchuser.png'
    url = sys.argv[0] + '?action=su'
    listitem = xbmcgui.ListItem(name, iconImage=icon_img)
    listitem.setInfo(type='video', infoLabels={'Title': name})
    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=listitem, isFolder=True)

def add_su_items(account, is_current):
    if is_current:
        name = '[COLOR yellow]%s (current)[/COLOR]' % (account)
    else:
        name = account
    icon_img =  os.path.dirname(__file__) + '/switchuser2.png'
    url = sys.argv[0] + '?action=set_login&login=' + account
    listitem = xbmcgui.ListItem(name, iconImage=icon_img)
    listitem.setInfo(type='video', infoLabels={'Title': name})
    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=listitem, isFolder=False)

def add_pseudo_items():
    name = '[SEARCH]'
    url = sys.argv[0] + '?action=search&query='
    listitem = xbmcgui.ListItem(name)
    listitem.setInfo(type='video', infoLabels={'Title': name})
    xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=listitem, isFolder=True)

    if __settings__.getSetting('recent_queries') != '':
        name = '[SEARCH HISTORY]'
        url = sys.argv[0] + '?action=search_history'
        listitem = xbmcgui.ListItem(name)
        listitem.setInfo(type='video', infoLabels={'Title': name})
        xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=listitem, isFolder=True)



def runner():
    # check if login and pass has been set
    if __settings__.getSetting('api_key') == '' or (__settings__.getSetting('login') == '' or __settings__.getSetting('password') == ''):
        if not __settings__.getSetting('auto_login'):
            resp = xbmcgui.Dialog().yesno("No username/password set!","Furk.net requires you to be logged in to view", \
                "videos.  Would you like to log-in now?")
            if resp:
                __settings__.openSettings()
            else:
                return
    
    # get params
    params = parse_qs(sys.argv[2][1:])
    for k in params:
        params[k] = params[k][0]
    xbmc.log("params=%s" % params)

    # show files list by default 
    if not params:
        params['action'] = 'root'

    # api obj is needed
    api_key = __settings__.getSetting('api_key')

    if(params['action'] == 'su'):
        now_user=__settings__.getSetting('login')
        other_user=__settings__.getSetting('other_login').split(' ')
        update_other_user=[]
        add_su_items(now_user, True)
        for account in other_user:
            if(account != other_user):
                update_other_user.append(account)
                add_su_items(account, False)
        __settings__.setSetting(id='other_login', value=' '.join(update_other_user))

        if api_key != '':
            api = FurkAPI(api_key)
            info = api.account_info()
            xbmc.log(json.dumps(info))
            net_stats = info['net_stats']
            bw_stats = info['bw_stats']
            for i in range(7):
                date_str = datetime.datetime.fromtimestamp(int(net_stats[i]['ts'][0:-3])).strftime('%m-%d')
                net_bytes = int(net_stats[i]['bytes'])
                bw_bytes = int(bw_stats[i]['bytes'])
                net_mb = int(math.ceil(float(net_bytes)/50000000))
                if net_mb > 20:
                    net_mb = 20
                bw_mb = int(math.ceil(float(bw_bytes)/50000000))
                if bw_mb > 20:
                    bw_mb = 20
                net_color = 'white'
                if net_mb >= 20:
                    net_color = 'red'
                elif net_mb >= 15:
                    net_color = 'orange'
                elif net_mb >= 10:
                    net_color = 'yellow'
                bw_color = 'white'
                if bw_mb >= 20:
                    bw_color = 'red'
                elif bw_mb >= 15:
                    bw_color = 'orange'
                elif bw_mb >= 10:
                    bw_color = 'yellow'

                name = "{0}: User: [COLOR {5}]{7}{1:.3f}[/COLOR] MB [COLOR {5}]{2}[/COLOR] IP: [COLOR {6}]{8}{3:.3f}[/COLOR] MB [COLOR {6}]{4}[/COLOR]".format(
                    date_str, float(bw_bytes/1000)/1000, '|'*bw_mb + '.'*(20-bw_mb), float(net_bytes/1000)/1000, '|'*net_mb+'.'*(20-net_mb), bw_color, net_color,
                    '0'*int(3 - int(bw_mb >= 1) - int(bw_mb >= 2) - int(bw_mb >= 20)),
                    '0'*int(3 - int(net_mb >= 1) - int(net_mb >= 2) - int(net_mb >= 20))
                  )
                url = sys.argv[0] + '?action=noop'
                listitem = xbmcgui.ListItem(name)
                xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=listitem, isFolder=False)


        xbmc.executebuiltin("Container.SetViewMode(51)") 
        xbmcplugin.endOfDirectory(pluginhandle)
        return

    if(params['action'] == 'set_login' and params['login'] != __settings__.getSetting('login')):
        now_user=__settings__.getSetting('login')
        new_login=params['login']
        other_user=__settings__.getSetting('other_login').split(' ')
        update_other_user=[now_user]
        valid_user = False
        for account in other_user:
            if(new_login == account):
                valid_user = True
            else:
                update_other_user.append(account)
        if(valid_user):
            __settings__.setSetting(id='login', value=new_login)
            __settings__.setSetting(id='other_login', value=' '.join(update_other_user))
            __settings__.setSetting(id='api_key', value='')
            xbmc.executebuiltin('Action(ParentDir)')
            xbmc.executebuiltin('Container.Refresh')

        return

        
    if api_key == '':
        api = FurkAPI()
        api_key = api.login(login=__settings__.getSetting('login'), pwd=__settings__.getSetting('password'))
        if(api_key):
            __settings__.setSetting('api_key', api_key)
        else:
            switch_user_items()
            xbmcplugin.endOfDirectory(pluginhandle)
            return
    else:
        api = FurkAPI(api_key)

    # menu listing
    # just play a file
    if(params['action'] == 'play'):
        xbmc.Player().play(urllib.unquote(params['url']))
        xbmcplugin.endOfDirectory(pluginhandle)
        return
    elif(params['action'] == 'unlink'):
        resp = xbmcgui.Dialog().yesno("Delete confirmation","Are you sure to delete this directory?")
        if resp:
            result = api.unlink({'id': params['id']})
            if(result.has_key('status') and result['status'] == 'ok'):
              xbmc.executebuiltin('Container.Refresh')
            else:
              xbmc.log(json.dumps(result))
              xbmcgui.Dialog().ok('Error Occured...', 'Please check the xbmc.log file for details...')

        return
    
    elif(params['action'] == 'download' or params['action'] == 'download_to' or params['action'] == 'download_dir' or params['action'] == 'download_dir_to'):
        url = urllib.unquote(params['url'])
        if params['action'] == 'download' or params['action'] == 'download_dir':
          save_dir = __settings__.getSetting('save_dir')
        need_refresh = False
        if params['action'] == 'download_to' or params['action'] == 'download_dir_to' or not os.path.isdir(str(save_dir)):
          need_refresh = True
          save_dir = xbmcgui.Dialog().browse(3, 'Select a path to save...', 'files')
        if not os.path.isdir(str(save_dir)):
          xbmcgui.Dialog().ok('Error Occured...', 'cannot access the directory: ', save_dir)
          return
        else:
          __settings__.setSetting(id='save_dir', value=save_dir)
        file_name = url.split('/')[-1]
        if params['rename'] == 'yes':
          file_name = re.sub(r'[^a-zA-Z0-9\.\-\(\)\~]+', '_', file_name)
          url_fix = url.split('/')
          url_fix[-1] = file_name
          url_fix = '/'.join(url_fix)
          url = url_fix
        if((params['action'] == 'download_dir' or params['action'] == 'download_dir_to') and not re.match('\.[a-zA-Z0-9]+$', file_name)):
          file_name = file_name + '.zip'
        try:
          fin = urllib2.urlopen(url)
        except Exception,e:
          xbmcgui.Dialog().ok('Error Occured...', str(e))
          return
        fout = open(save_dir+file_name, 'wb')
        xbmc.log(json.dumps(fin.getcode()))
        meta = fin.info()
        content_length = meta.getheaders("Content-Length")
        if len(content_length) > 0:
          file_size = int(meta.getheaders("Content-Length")[0])
        else:
          file_size = -1;
        dialog = xbmcgui.DialogProgress()
        if file_size != -1:
          dialog.create('Downloading...',"{0}".format(file_name), 'Total: {0} Bytes'.format(format(file_size, ',')))
        else:
          dialog.create('Downloading...',"{0}".format(file_name), 'Total: ??? Bytes')

        file_size_dl = 0
        block_sz = (1 << 20)
        while True:
            buffer = fin.read(block_sz)
            if dialog.iscanceled():
              os.remove(save_dir+file_name)
              break
            if not buffer:
              break

            file_size_dl += len(buffer)
            fout.write(buffer)
            if file_size != -1:
              percent = float(file_size_dl) / file_size
              dialog.update(file_size_dl*100 / file_size , 
                "Downloading: {0}".format(file_name), 
                'Total: {0} Bytes'.format(format(file_size, ',')),
                '  Now: {0} Bytes ({1:.2%})'.format(format(file_size_dl, ','), percent))
            else:
              percent = 0
              dialog.update(percent , 
                "Downloading: {0}".format(file_name), 
                'Total: ??? Bytes',
                '  Now: {0} Bytes ({1:.2%})'.format(format(file_size_dl, ','), 0))

        fout.close()
        dialog.close()
        if not dialog.iscanceled():
          xbmcgui.Dialog().ok('Download Success...', format(file_size_dl, ',')+' bytes downloaded...')
        if need_refresh:        
          xbmc.executebuiltin('Container.Refresh')
        xbmcplugin.endOfDirectory(pluginhandle)
        return

    # root menu
    if(params['action'] == 'root'):
        files = api.file_get()
        if (__settings__.getSetting('enable_search') != 'false'):
            add_pseudo_items()
        if not files:
            return
        xbmc.log(json.dumps(files[0]))
        for fl in files:
            url = sys.argv[0] + '?action=file&id=' + fl['id']
            listitem = xbmcgui.ListItem(fl['name']+(' ({0:.1f} MB)'.format(float(int(fl['size'])/100000)/10)))
            if fl.has_key('ss_urls_tn'):
                listitem.setThumbnailImage(fl['ss_urls_tn'][0]);
                listitem.setProperty('fanart_image', fl['ss_urls_tn'][0])
            listitem.setInfo(type='video', infoLabels={'title': fl['name'], 'size': int(fl['size'])})
            url_dl = sys.argv[0] + '?action=download_dir&rename=no&url=' + fl['url_dl']
            url_dl_to = sys.argv[0] + '?action=download_dir_to&rename=no&url=' + fl['url_dl']
            url_dl_encode = sys.argv[0] + '?action=download_dir&rename=yes&url=' + fl['url_dl']
            url_unlink = sys.argv[0] + '?action=unlink&id=' + fl['id']
            context_menu_list = [
              ('Download...', 'XBMC.RunPlugin('+url_dl_to+')')
              ]
            save_dir = __settings__.getSetting('save_dir')
            if os.path.isdir(str(save_dir)):
              context_menu_list.append(('Download to '+save_dir, 'XBMC.RunPlugin('+url_dl+')'))
            context_menu_list.append(('Normalize filename', 'XBMC.RunPlugin('+url_dl_encode+')'))
            context_menu_list.append(('Delete this Directory', 'XBMC.RunPlugin('+url_unlink+')'))
            listitem.addContextMenuItems(context_menu_list, replaceItems=True)
            xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=listitem, isFolder=True)
        
        if __settings__.getSetting('other_login') != '':
            switch_user_items()

        xbmcplugin.endOfDirectory(pluginhandle)

    elif(params['action'] == 'file'):
        f = api.file_get({'id': params['id'], 't_files': 1})[0]
        t_files = f['t_files']
        for item in t_files:
            if not re.match('^(audio|video|image)/', item['ct']):
                continue
            url = sys.argv[0] + '?action=play&url=' + item['url_dl']
            url_dl = sys.argv[0] + '?action=download&rename=no&url=' + item['url_dl']
            url_dl_to = sys.argv[0] + '?action=download_to&rename=no&url=' + item['url_dl']
            context_menu_list = [
              ('Download...', 'XBMC.RunPlugin('+url_dl_to+')')
              ]
            save_dir = __settings__.getSetting('save_dir')
            if os.path.isdir(str(save_dir)):
              context_menu_list.append(('Download to '+save_dir, 'XBMC.RunPlugin('+url_dl+')'))
            name = item['name']
            if item.has_key('bitrate'):
                name = '%s %skb/s' % (item['name'], item['bitrate'])
            listitem = xbmcgui.ListItem(name)
            if item.has_key('ss_urls_tn'):
                listitem.setThumbnailImage(item['ss_urls_tn'][0]);
                listitem.setProperty('fanart_image', item['ss_urls_tn'][0])
            if re.match('^(audio|video)/', item['ct']):
              listitem.setInfo('video', {'title': name, 'size': int(item['size']), 'duration': item['length']})
            elif re.match('^(image)/', item['ct']):
              listitem.setThumbnailImage('DefaultPicture.png');

            listitem.addContextMenuItems(context_menu_list, replaceItems=True)

            xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=listitem, isFolder=False)
        ss_files = f['ss_urls']
        sst_files = f['ss_urls_tn']
        for i in range(len(ss_files)):
            ss = ss_files[i]
            sst = sst_files[i]
            listitem = xbmcgui.ListItem('[COLOR FF66AAFF]Screenshot '+str(i)+'[/COLOR]')
            listitem.setThumbnailImage(sst)
            listitem.setProperty('fanart_image', sst)
            xbmcplugin.addDirectoryItem(handle=pluginhandle, url=sys.argv[0]+'?action=noop', listitem=listitem, isFolder=False)

        xbmc.executebuiltin("Container.SetViewMode(508)") 
        xbmcplugin.endOfDirectory(pluginhandle)

    elif(params['action'] == 'search_history'):
        if __settings__.getSetting('recent_queries') == '':
            return

        recent = __settings__.getSetting('recent_queries').split('|')
        if '' in recent:
            recent.remove('')
            total = len(recent) + 1
        for r in recent:
            name = urllib.unquote(r)
            url = sys.argv[0] + '?action=search&q=' + r

            listitem = xbmcgui.ListItem(name)
            listitem.setInfo(type='video', infoLabels={'Title': name})
            xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=listitem, isFolder=True)
        xbmcplugin.endOfDirectory(pluginhandle)

    elif(params['action'] == 'search'):
        if not params.has_key('q'):
            params['q'] = ''
        keyboard = xbmc.Keyboard(urllib.unquote(params['q']), 'Search')
        keyboard.doModal()
        
        if not keyboard.isConfirmed():
            print 'not confirmed'
            return

        params['q'] = keyboard.getText()
        files = api.metasearch({'q': params['q']})
        if not files:
            xbmcgui.Dialog().ok('No results', 'No results')
            return

        # add history
        recent = __settings__.getSetting('recent_queries').split('|')
        recent = [ urllib.unquote(r) for r in recent ]
        if params['q'] in recent:
            recent.remove(params['q'])
        recent.insert(0, params['q'])
        recent = [ urllib.quote(r) for r in recent ]
        __settings__.setSetting(id='recent_queries', value='|'.join(recent))

        if (__settings__.getSetting('enable_search') != 'false'):
            add_pseudo_items()
        for item in files:
            url = sys.argv[0] + '?action=file&id=' + item['id']
            listitem = xbmcgui.ListItem(item['name'])
            if item.has_key('ss_urls_tn'):
                listitem.setThumbnailImage(item['ss_urls_tn'][0]);
                listitem.setProperty('fanart_image', item['ss_urls_tn'][0])
            listitem.setInfo(type='video', infoLabels={'title': item['name'], 'size': int(item['size'])})
            xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=listitem, isFolder=True)
        
        xbmcplugin.endOfDirectory(pluginhandle)

    elif(params['action'] == 'search_history'):
        recent = __settings__.getSetting('recent_queries').split('|')
        if '' in recent:
            recent.remove('')
            total = len(recent) + 1

        for r in recent:
            name = urllib.unquote(r)
            url = sys.argv[0] + '?action=search&q=' + r

            listitem = xbmcgui.ListItem(name)
            listitem.setInfo(type='video', infoLabels={'Title': name})
            xbmcplugin.addDirectoryItem(handle=pluginhandle, url=url, listitem=listitem, isFolder=True)

        xbmcplugin.endOfDirectory(pluginhandle)


if __name__ == "__main__":
    runner()
            


sys.modules.clear()



