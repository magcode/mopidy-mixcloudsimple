import logging
import requests
import json
import pykka
from yt_dlp import YoutubeDL
from datetime import datetime
from mopidy.models import Ref,Track,Album,Image,Artist
from mopidy.backend import *

logger = logging.getLogger(__name__)
mc_uri='mixcloudsimple:'
mc_uri_root=mc_uri+'root'
mc_uri_stream=mc_uri+'stream'
mx_api='https://api.mixcloud.com'
latestShowsLabel='   Latest Shows'

class MixcloudSimpleBackend(pykka.ThreadingActor, Backend):
    uri_schemes = [u'mixcloudsimple']
 
    def __init__(self, config, audio):
        super(MixcloudSimpleBackend, self).__init__()        
        self.library = MixcloudSimpleLibrary(self,config)
        self.playback = MixcloudSimplePlaybackProvider(audio=audio, backend=self)        
        
class MixcloudSimpleLibrary(LibraryProvider):
    root_directory = Ref.directory(uri=mc_uri_root, name='Mixcloud')
    
    def __init__(self, backend, config):
        super(MixcloudSimpleLibrary, self).__init__(backend)
        self.imageCache = {}
        self.trackCache = {}
        self.refCache = {}
        self.mxaccount = config['mixcloudsimple']['account']
        self.lastRefresh = datetime.now()
        self.cacheTimeMin = 60*24
 
    def browse(self, uri):
      refs = []
      now = datetime.now()
      minutesSinceLastLoad = round((now - self.lastRefresh).total_seconds() / 60)
      logger.info("Uri browse (" + uri + "). Data is " + str(minutesSinceLastLoad) + " min old. Last refresh was " + self.lastRefresh.strftime("%d/%m/%Y %H:%M:%S"))
      if (minutesSinceLastLoad > self.cacheTimeMin):
          self.refresh('')
          self.lastRefresh = now
          logger.info("Clearing cache ... ")
      
      # root
      if uri==mc_uri_root:
        # try the cache first
        if uri in self.refCache and self.refCache[uri]:
          refs = self.refCache[uri]
        else:
          refs = self.loadRootAlbumRefs()

      # stream
      elif uri==mc_uri_stream:
        # try the cache first
        if uri in self.refCache and self.refCache[uri]:
          refs = self.refCache[uri]
        else:
          refs = self.loadTrackRefsFromStream()    
          
      # user tracks
      else:
        # try the cache first
        if uri in self.refCache and self.refCache[uri]:
          refs = self.refCache[uri]
        else:
          refs = self.loadTrackRefsFromUser(uri)
      return refs

    def loadTrackRefsFromStream(self):
      # get a copy of all our track ref's
      refsCopy=[]
      rootRefs = self.browse(mc_uri_root)
      for rootRef in rootRefs:
        if rootRef.uri != mc_uri_stream:
          userTrackRefs = self.browse(rootRef.uri)
          refsCopy = refsCopy + userTrackRefs

      # sort this copy by date
      refsCopy.sort(key=lambda x: self.trackCache[x.uri].date, reverse=True)
      refs=[]
      trackNo = 0
      for ref in refsCopy:
        originalUri = ref.uri
        newUri = mc_uri_stream + originalUri.lstrip(mc_uri)
        streamTrackRef = Ref.track(name=ref.name, uri=newUri)
        refs.append(streamTrackRef)
        # copy the Track with new URI and with new naming
        trackNo += 1        
        originalTrack = self.trackCache[originalUri]
        newName = str(trackNo).zfill(2) + ". " + originalTrack.name[4:]
        track=Track(uri=newUri,name=newName,album=originalTrack.album,artists=originalTrack.artists,length=originalTrack.length,date=originalTrack.date)
        self.trackCache[newUri] = track
        # copy the image
        self.imageCache[newUri] = self.imageCache[originalUri]
      
      # lets limit to 99 tracks. Should be enough
      return refs[:99]
    
    def loadRootAlbumRefs(self):
      refs=[]
      
      # latest shows
      r =requests.get(mx_api + "/" + self.mxaccount,timeout=10)
      logger.info("Loading root")
      jsono = json.loads(r.text)
      ref = Ref.directory(name=latestShowsLabel, uri=mc_uri_stream)
      imguri = jsono['pictures']['320wx320h']
      self.imageCache[mc_uri_stream] = Image(uri=imguri)
      refs.append(ref)
      
      # following's tracks
      r =requests.get(mx_api + "/" + self.mxaccount + '/following/',timeout=10)
      logger.info("Loading followings")
      jsono = json.loads(r.text)
      for p in jsono['data']:
        accounturi = mc_uri + p['key']
        ref = Ref.directory(name=p['name'], uri=accounturi)
        self.imageCache[accounturi] = Image(uri=p['pictures']['320wx320h'])
        refs.append(ref)
      self.refCache[mc_uri_root] = refs
      return refs

    def loadTrackRefsFromUser(self, uri):
      refs=[]
      user = uri.strip(mc_uri)
      logger.info("Loading tracks of user " + user)
      r =requests.get(mx_api + user + 'cloudcasts/',timeout=10)
      jsono = json.loads(r.text)
      trackNo = 0
      for p in jsono['data']:
        trackNo += 1      
        trackuri=mc_uri + p['url']
        ref=Ref.track(name=p['name'], uri=trackuri)
        refs.append(ref)
        self.imageCache[trackuri] = Image(uri=p['pictures']['320wx320h'])
        len=int(p['audio_length'])*1000
        album=Album(name='Mixcloud')
        artist=Artist(uri='none',name=p['user']['name'])
        dateString = p['created_time']
        # date format from mixcloud is "2019-12-06T14:21:13Z"
        dateObj = datetime.strptime(dateString, '%Y-%m-%dT%H:%M:%SZ')
        dateStringMop = dateObj.strftime("%Y-%m-%d")
        # synthetic name for proper sorting in Iris UI
        synName = str(trackNo).zfill(2) + '. ' + p['name']
        track=Track(uri=trackuri,name=synName,album=album,artists=[artist],length=len,date=dateStringMop,track_no=trackNo)
        self.trackCache[trackuri] = track
      self.refCache[uri] = refs
      return refs
      
    def refresh(self, uri):
      logger.info("refreshing for uri: " + uri)
      if uri == mc_uri_stream or uri == '':
        # we need to flush everything
        self.refCache = {}
      else:
        self.refCache[uri] = None
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
      mxUrl = uri.lstrip(mc_uri_stream)
      mxUrl = mxUrl.lstrip(mc_uri)
      info = YoutubeDL().extract_info(
                url=mxUrl,
                download=False,
                ie_key="Mixcloud",
                extra_info={},
                force_generic_extractor=False)      
      return info['url']
