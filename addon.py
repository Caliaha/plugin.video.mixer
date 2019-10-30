import sys
import urllib
import urllib2
import urlparse
import re
import xbmcaddon
import xbmcplugin
import xbmcgui
import json

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

addon = xbmcaddon.Addon()


playbackQuality = addon.getSetting('preferredQuality')

def debug(list):
	xbmcgui.Dialog().ok("Mixer", "\n".join(list))

def CATEGORIES():
	addDir('Top Streams','', 'topstreams','')
	addDir('Browse Games', '', 'games', '')
                       
def INDEX(url):
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0')
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()
        match=re.compile('<tr><td>(.+?)</td><td>(.+?)</td><td>(.+?)</td><td>(.+?)</td></tr>').findall(link)
        for name,thumbnail,summary,url in match:
                addDir(name,url,2,thumbnail)

def TOPSTREAMS(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	data = json.loads(link)
	for streamer in data:
		addStreamer(streamer)

def addStreamer(streamer):
	#debug([str(streamer["id"]), str(streamer["token"]), streamer["type"]["coverUrl"]])
	
	#u=url
	name = streamer["token"]
	id = str(streamer["id"]) or ""
	title = streamer["name"] or ""
	game = streamer["type"]["name"] or ""
	thumbnail = streamer["type"]["coverUrl"] or ""
	description = streamer["type"]["description"] or ""
	currentViewers = str(streamer["viewersCurrent"]) or ""
	
	u=base_url+"?broadcastID="+urllib.quote_plus(id)+"&mode=playStream&name="+urllib.quote_plus(name)+"&thumbnail="+urllib.quote_plus(thumbnail)
	
	liz=xbmcgui.ListItem(name + ' - ' + title, iconImage="DefaultVideo.png", thumbnailImage=streamer["type"]["coverUrl"])
	if "bannerUrl" in streamer:
		liz.setArt({'fanart': streamer["bannerUrl"]})
	else:
		liz.setArt({'fanart': streamer["type"]["backgroundUrl"]})
	liz.setInfo( type="Video", infoLabels={ "Title": name + ' - ' + title, "Plot": 'Viewers: ' + currentViewers + '\n' + game + '\n' + description } )
	return xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz)



def addDir(name,url,mode,iconimage):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	ok=xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=True)
	return ok

def paginate(url, start):
	urlP = url + "?page=" + str(start) + "&language=en"
	xbmcplugin.setContent(addon_handle, 'videos')
	TOPSTREAMS(urlP)
	liz=xbmcgui.ListItem("Next Page", iconImage="DefaultFolder.png")
	#liz.setInfo( type="Video", infoLabels={ "Title": name } )
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=base_url + '?mode=topstreams&page=' + str(int(start) + 1),listitem=liz,isFolder=True)

def searchGames(url, query, start):
	limit = 32
	urlP = url + "&limit=" + str(limit) + "&page=" + str(start) + "&query=" + query
	xbmcplugin.setContent(addon_handle, 'videos')
	req = urllib2.Request(urlP)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	data = json.loads(link)
	count = 0
	for game in data:
		count = count + 1
		gameID = str(game["id"]) or "" # Probably should just skip if this happens
		thumbnail = game["coverUrl"] or ""
		u=base_url+"?gameID="+urllib.quote_plus(gameID)+"&mode=game&thumbnail="+urllib.quote_plus(thumbnail)
		title = game["name"] or ""
		currentViewers = str(game["viewersCurrent"]) or ""
		liz=xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=game["coverUrl"])
		liz.setArt({'fanart': game["backgroundUrl"]})
		liz.setInfo( type="Video", infoLabels={ "Title": title, "Plot": 'Viewers: ' + currentViewers } )
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=True)
	if count >= limit:
		liz=xbmcgui.ListItem("Next Page", iconImage="DefaultFolder.png")
		#liz.setInfo( type="Video", infoLabels={ "Title": name } )
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=base_url + '?mode=games&page=' + str(int(start) + 1) + '&query=' + query,listitem=liz,isFolder=True)

def listGame(gameID, start):
	limit = 52 # Make a setting later FIXME
	#https://mixer.com/api/v1/channels?where=typeId:eq:568925&limit=52&page=0&order=online:desc,viewersCurrent:desc&noCount=1
	urlP = 'https://mixer.com/api/v1/channels?where=typeId:eq:' + gameID + "&limit=" + str(limit) + "&page=" + str(start) + '&order=online:desc,viewersCurrent:desc&noCount=1'
	xbmcplugin.setContent(addon_handle, 'videos')
	req = urllib2.Request(urlP)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	data = json.loads(link)
	count = 0
	for streamer in data:
		addStreamer(streamer)
		count = count + 1
	
	#liz.setInfo( type="Video", infoLabels={ "Title": name } )
	if count >= limit: # Only show next if needed
		liz=xbmcgui.ListItem("Next Page", iconImage="DefaultFolder.png")
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=base_url + '?mode=game&page=' + str(int(start) + 1) + '&gameID=' + gameID,listitem=liz,isFolder=True)
	pass
	

def streamerInfo(broadcastID, thumbnail, video):
	url = 'https://mixer.com/api/v1/channels/' + str(broadcastID) + '/details'
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	data = json.loads(link)
	li = xbmcgui.ListItem(path=video, thumbnailImage=thumbnail)
	li.setInfo(type="Video", infoLabels={"Title":data['token'] + ' - ' + data['name'] + ' - ' + str(data['viewersCurrent']), "Plot": data['type']['description']})
	
	return li

def selectPreferredOrLowerQuality(qualities):
	if playbackQuality in qualities:
		return qualities[playbackQuality]
	
	currentQuality = 0
	for quality in qualities:
		if quality > currentQuality <= playbackQuality:
			currentQuality = quality
	
	return qualities[currentQuality]

def fetchManifest(broadcastID, thumbnail):
	url = 'https://mixer.com/api/v1/channels/' + str(broadcastID) + '/manifest.m3u8'
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	#https://videocdn.mixer.com/hls/90571077-73518d48d203e1564251a530245f253e_720p/index.m3u8
	#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=4000000,RESOLUTION=1920x1080,NAME=source(1080p)
	#https://videocdn.mixer.com/hls/90571077-73518d48d203e1564251a530245f253e_source/index.m3u8
	videos = re.compile('EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=(.*?),RESOLUTION=(.*?),NAME=(.*?)\n(.*?)\n').findall(link)
	#videos = re.compile('(https://videocdn.mixer.com/hls/.*?_720p/index.m3u8)').findall(link)
	qualities = { }
	for quality in videos:
		qualityName = "".join(i for i in quality[2] if i.isdigit())
		#xbmcgui.Dialog().ok("MixerTest", qualityName + '\n' + quality[3])
		qualities[qualityName] = quality[3]
	
	videoURL = selectPreferredOrLowerQuality(qualities)
	
	#for video in videos:
		#xbmcgui.Dialog().ok("MixerTest", video)
		#li = xbmcgui.ListItem(path=video, thumbnailImage=thumbnail)
	li = streamerInfo(broadcastID, thumbnail, videoURL)

	xbmcplugin.setResolvedUrl(addon_handle, True, listitem = li)
	xbmc.Player().play(videoURL, li) 
		#return video


mode = args.get('mode', None)
url = args.get('url', None)
broadcastID = args.get('broadcastID', None)

print "Mode: "+str(mode)
print "URL: "+str(url)

#xbmcgui.Dialog().ok("MixerTest", str(mode) + str(url) + '\n' + str(type(url)))

if not mode:
	CATEGORIES()

if mode:
	if mode[0] == "topstreams":
		page = args.get('page', [0])
		paginate("https://mixer.com/api/v1/delve/topStreams", page[0])
	if mode[0] == "game":
		gameID = args.get('gameID', None)
		page = args.get('page', [0])
		listGame(gameID[0], page[0])
	if mode[0] == "games":
		page = args.get('page', [0])
		query = args.get('query', [''])
		searchGames("https://mixer.com/api/v1/types?order=viewersCurrent:desc&noCount=1", query[0], page[0])
	if mode[0] == "playStream" and broadcastID:
		thumbnail = args.get('thumbnail', None)
		#xbmcgui.Dialog().ok("MixerTest", str(broadcastID))
		fetchManifest(broadcastID[0], thumbnail[0])



xbmcplugin.endOfDirectory(addon_handle)
