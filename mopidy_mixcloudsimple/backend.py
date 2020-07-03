import logging
import pathlib
import threading
import requests
import json
import pykka
import youtube_dl
from mopidy.models import Ref,Track,Album,SearchResult,Artist,Image,Playlist
from mopidy.backend import *

logger = logging.getLogger(__name__)
mcs_uri='mixcloudsimple:'
mcs_uri_root=mcs_uri+'root'
mx_api='https://api.mixcloud.com/'

class MixcloudSimpleBackend(pykka.ThreadingActor, Backend):
    uri_schemes = [u'mixcloudsimple']
 
    def __init__(self, config, audio):
        super(MixcloudSimpleBackend, self).__init__()        
        self.library = MixcloudSimpleLibrary(self,config)
        self.playback = MixcloudSimplePlaybackProvider(audio=audio, backend=self)        
        
class MixcloudSimpleLibrary(LibraryProvider):
    root_directory = Ref.directory(uri=mcs_uri_root, name='Mixcloud (Simple)')
    
    def __init__(self, backend, config):
        super(MixcloudSimpleLibrary, self).__init__(backend)
        self.imageCache = {}
        self.trackCache = {}
        self.mxaccount = config['mixcloudsimple']['account']        
 
    def browse(self, uri):    
      refs=[]
      if uri==mcs_uri_root:
        r =requests.get(mx_api + self.mxaccount + '/following/',timeout=10)
        jsono = json.loads(r.text)
        for p in jsono['data']:
          accounturi = mcs_uri + p['key']
          ref = Ref.album(name=p['name'], uri=accounturi)
          self.imageCache[accounturi] = Image(uri=p['pictures']['320wx320h'])
          refs.append(ref)
      else:
        user = uri.strip(mcs_uri)
        r =requests.get(mx_api + user + 'cloudcasts/',timeout=10)
        jsono = json.loads(r.text)
        for p in jsono['data']:        
          trackuri="mixcloudsimple:" + p['url']
          ref=Ref.track(name=p['name'], uri=trackuri)
          refs.append(ref)          
          self.imageCache[trackuri] = Image(uri=p['pictures']['320wx320h'])
          len=int(p['audio_length'])*1000
          album=Album(name='Mixcloud')
          artist=Artist(uri='none',name=p['user']['name'])
          track=Track(uri=trackuri,name=p['name'],album=album,artists=[artist],length=len)
          self.trackCache[trackuri] = track
      return refs
      
    def refresh(self, uri=None):
      self.imageCache = {}
      self.trackCache = {}
      return

    def lookup(self, uri, uris=None):
      if uri in self.trackCache:
        track=self.trackCache[uri]
        return [track]
      else:
        return []

    def get_images(self, uris):
      
      ret={}
      for uri in uris:
        if uri in self.imageCache:
          img=self.imageCache[uri]
          if img is not None: 
            ret[uri]=[img]
      return ret

    def search(self, query=None, uris=None, exact=False):
      return {}

class MixcloudSimplePlaybackProvider(PlaybackProvider):
    def translate_uri(self, uri):
      mxUrl = uri.strip(mcs_uri)
      info = youtube_dl.YoutubeDL().extract_info(
                url=mxUrl,
                download=False,
                ie_key="Mixcloud",
                extra_info={},
                force_generic_extractor=False)      
      return info['url']
