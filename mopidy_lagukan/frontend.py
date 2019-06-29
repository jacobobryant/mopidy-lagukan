from __future__ import print_function

import pykka

from mopidy import core, httpclient
import cPickle as pickle
import edn_format
import appdirs
import os
import time
import uuid
import requests
import json
import logging

logger = logging.getLogger(__name__)

# todo send collection in (rate-limited) batches
# todo handle invalid client id

auth_url = "https://securetoken.googleapis.com/v1/token?key=AIzaSyCMIaf1mHHyJziOI0xRw0Qgw6Bh5f5UUS8"
backend_url = "https://79gcws2i5i.execute-api.us-east-1.amazonaws.com/dev"
#backend_url = "http://localhost:8080"
streaming_sources = {'soundcloud', 'spotify', 'gmusic', 'youtube'}
collection_uris = {'local:directory'}

def get_session(config):
    proxy = httpclient.format_proxy(config['proxy'])
    user_agent = httpclient.format_user_agent('Mopidy-Lagukan/0.1.2')

    session = requests.Session()
    session.proxies.update({'http': proxy, 'https': proxy})
    session.headers.update({'user-agent': user_agent})

    return session

def select_keys(d, keys):
    return {k: d[k] for k in keys if k in d}

def stringify_keys(d):
    return {k.name: d[k] for k in d}

def collect(library, uri):
    ret = []
    for ref in library.browse(uri).get():
        if ref.type == 'directory':
            ret.extend(collect(library, ref.uri))
        elif ref.type == 'track':
            ret.append(ref.uri)
    return ret

def format_track(track):
    ret = {'track/title': track.name}
    if track.album != None:
        ret['track/album'] = track.album.name
        if track.album.artists != None:
            ret['track/artists'] = [artist.name for artist in track.album.artists]
    return ret

class LagukanFrontend(pykka.ThreadingActor, core.CoreListener):
    def __init__(self, config, core):
        super(LagukanFrontend, self).__init__()
        self.core = core
        self.config = config
        self.session = get_session(config)
        self.expire_time = None
        self.update_token()

        state_file = os.path.join(appdirs.user_data_dir(), 'mopidy-lagukan', 'state')
        try:
            with open(state_file, 'r') as f:
                state = pickle.load(f)
        except:
            state = select_keys(self.hit('/register-client'), ['client-id'])

        if 'last-refresh' not in state or time.time() - state['last-refresh'] > 60 * 60 * 24 * 7:
            state['last-refresh'] = time.time()

            collection = []
            for collection_uri in collection_uris:
                collection.extend(collect(core.library, collection_uri))
            collection = [format_track(track)
                          for result in core.library.lookup(uris=collection).get().values()
                          for track in result]

            sources = [k for k in config.keys()
                         if k in streaming_sources and config[k]['enabled']]

            # todo spotify uid and lastfm uid
            state['collection'] = collection
            state['sources'] = sources

            self.hit('/init', select_keys(state, ['client-id', 'collection', 'sources']))

            try:
                os.makedirs(os.path.dirname(state_file))
            except:
                pass

            with open(state_file, 'w') as f:
                pickle.dump(select_keys(state, ['client-id', 'last-refresh']), f, pickle.HIGHEST_PROTOCOL)

        self.client_id = state['client-id']
        # TODO modify tracklist
        self.recommend()

    def recommend(self, events=None):
        if events is None:
            events = []
        metas = self.hit('/recommend', {'client-id': self.client_id, 'events': events})['recommendations']
        tracks = [self.get_track(m) for m in metas]
        tracks = [x for x in tracks if x is not None]
        current_pos = self.core.tracklist.index().get()
        pos = 0 if current_pos == None else current_pos + 1
        self.core.tracklist.add(tracks=tracks, at_position=pos)

    def hit(self, url, payload=None):
        logger.info("hitting Lagukan endpoint: " + url)
        self.update_token()

        url = backend_url + url
        payload = edn_format.dumps(payload, keyword_keys=True)
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Content-Type': 'application/edn',
                   'Accept': 'application/json'}

        response = self.session.post(url, data=payload, headers=headers)
        response.raise_for_status()
        #import code; code.interact(local=locals())
        return json.loads(response.text)

    def update_token(self):
        if not self.expire_time or self.expire_time < time.time() + 60 * 10:
            response = self.session.post(auth_url,
                    {'grant_type': 'refresh_token', 'refresh_token': self.config['lagukan']['token']},
                    headers={'Cache-Control': 'no-cache', 'Origin': 'https://lagukan.com'}).json()
            self.token = response['access_token']
            self.expire_time = time.time() + int(response['expires_in'])

    def track_playback_ended(self, tl_track, time_position):
        events = [{'event.track-end/track': format_track(tl_track.track),
                   'event.track-end/length': tl_track.track.length,
                   'event.track-end/position': time_position}]
        self.recommend(events)

    def get_track(self, meta):
        try:
            query = {}
            for k, qk in zip(['track/artists', 'track/title', 'track/album'], ['artist', 'track_name', 'album']):
                if k in meta:
                    val = meta[k]
                    if k != 'track/artists':
                        val = [val]
                    query[qk] = val

            return self.core.library.search(query).get()[0].tracks[0]
        except:
            return None

        #import code; code.interact(local=locals())
