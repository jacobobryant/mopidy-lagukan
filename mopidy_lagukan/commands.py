from __future__ import print_function
from __future__ import unicode_literals
from oauth2client.client import OAuth2WebServerFlow
import gmusicapi
from dialog import Dialog
from os.path import expanduser, join, isdir, dirname
from os import makedirs
import webbrowser
from mopidy import commands
import sys

class LagukanCommand(commands.Command):
    def __init__(self):
        super(LagukanCommand, self).__init__()
        self.add_child('config', ConfigCommand())

def get_dir(d):
    code, result = d.dselect(expanduser("~") + '/', 10, 10)
    if code == d.OK and not isdir(result):
        d.msgbox(result + " is not a valid directory.")
        return get_dir(d)
    return (code, result)

def get_spotify_config(d):
    code, username = d.inputbox('Enter your Spotify username:\n\n'
            '(If you created your account with Facebook, see '
            'https://github.com/mopidy/mopidy-spotify#dependencies)', 10, 58)
    if code != d.OK:
        return

    code, password = d.passwordbox('Enter your Spotify password:\n\n'
            '(This is a requirement of libspotify. Your password is never sent to Lagukan.)',
            insecure=True)
    if code != d.OK:
        return

    webbrowser.open('https://www.mopidy.com/authenticate/#spotify')
    code, client_id = d.inputbox('Go to mopidy.com/authenticate and log in '
            'with Spotify. Then enter your client_id (Ctrl-Shift-V to paste):',
            10, 58)
    if code != d.OK:
        return

    code, client_secret = d.inputbox('Enter your client_secret from mopidy.com/authenticate'
            ' (Ctrl-Shift-V to paste):', 10, 58)
    if code != d.OK:
        return
    else:
        return {'username': username,
                'password': password,
                'client_id': client_id,
                'client_secret': client_secret}

def get_config(d):
    code, tags = d.checklist("Which music sources would you like to enable?",
            choices=[("Local collection", "", True),
                ("Spotify", "", False),
                ("Google Play Music", "", False)])

    if code != d.OK:
        print("Configuration unsuccessful.")
        sys.exit(1)

    local = 'Local collection' in tags
    spotify = 'Spotify' in tags
    gmusic = 'Google Play Music' in tags

    config = {}
    if local:
        d.msgbox("In the next dialog, enter the location of your local music collection.")
        code, result = get_dir(d)
        if code == d.OK:
            config['local'] = {'media_dir': result}
        else:
            return get_config(d)

    if spotify:
        conf = get_spotify_config(d)
        if conf is not None:
            config['spotify'] = conf
        else:
            return get_config(d)

    if gmusic:
        oauth_info = gmusicapi.Mobileclient._session_class.oauth
        flow = OAuth2WebServerFlow(**oauth_info._asdict())
        url = flow.step1_get_authorize_url()
        webbrowser.open(url)
        code, auth_code = d.inputbox('Authenticate with Google Play Music, then enter '
                'your code (Ctrl-Shift-V to paste):\n\n'
                '(Note: a page should have just opened in your web browser)', 10, 65)
        if code == d.OK:
            token = flow.step2_exchange(auth_code).refresh_token
            config['gmusic'] = {'refresh_token': token}
        else:
            return get_config(d)

    if 'local' not in config:
        config['local'] = {'enabled': 'false'}
    if 'spotify' not in config:
        config['spotify'] = {'enabled': 'false'}
        config['spotify_web'] = {'enabled': 'false'}
    else:
        config['spotify_web'] = {'client_id': config['spotify']['client_id'],
                                 'client_secret': config['spotify']['client_secret']}
    if 'gmusic' not in config:
        config['gmusic'] = {'enabled': 'false'}

    return config

class ConfigCommand(commands.Command):
    def run(self, args, config):
        d = Dialog()
        d.set_background_title('Lagukan config')
        config = get_config(d)
        config_file = join(expanduser("~"), ".config", "lagukan", "lagukan.conf")
        try:
            makedirs(dirname(config_file))
        except:
            pass
        with open(config_file, 'w') as f:
            for section in config:
                print('[' + section + ']', file=f)
                for k in config[section]:
                    print(k, '=', config[section][k], file=f)
                print(file=f)

        if 'local' in config and 'enabled' not in config['local']:
            sys.argv[1:] = ['--config', str(config_file), 'local', 'scan']
            import mopidy.__main__
            mopidy.__main__.main()
