import sys
import urllib
import urllib2
import urlparse
import re
import xbmcaddon
import xbmcplugin
import xbmcgui
import json
import pickle

addon = xbmcaddon.Addon()

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

PROFILE = xbmc.translatePath(addon.getAddonInfo('profile')).decode('utf-8')

playbackQuality = int(addon.getSetting('preferredQuality') or 0)
searchHistoryAmount = int(addon.getSetting('searchHistoryAmount') or 24)

if playbackQuality == 0:
	playbackQuality = 1080
	addon.setSetting('preferredQuality', '1080')



def debug(list):
	if type(list) == 'list':
		string = "\n".join(list)
	else:
		string = str(list)
	xbmcgui.Dialog().ok("Mixer", string)

def getUserInput(title, hidden=False):
	kb = xbmc.Keyboard('default', 'heading')
	kb.setDefault('')
	kb.setHeading(title)
	kb.setHiddenInput(hidden)
	kb.doModal()
	if (kb.isConfirmed()):
		return kb.getText()
	return None

def CATEGORIES():
	addDir('Top Streams','', 'topstreams','')
	addDir('Browse Games', '', 'games', '')
	addDir('Search', '', 'search', '')

def SEARCH():
	addDir('Search Games', '', 'search', '', { 'category': 'games' })
	addDir('Search Channel Names', '', 'search', '', { 'category': 'channels', 'scope': 'names' })
	addDir('Search Channel All', '', 'search', '', { 'category': 'channels', 'scope': 'all' })

def TOPSTREAMS(url):
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	data = json.loads(link)
	for streamer in data:
		addStreamer(streamer)

def getSearchHistory(category):
	try:
		file = open(PROFILE + category + '.txt', 'rb')
		searchHistory = pickle.load(file)
		file.close()
	except:
		searchHistory = [ ]

	return searchHistory

def addToSearchHistory(category, searchTerm):
	searchHistory = getSearchHistory(category)
	searchHistory.insert(0, searchTerm)
	while len(searchHistory) > searchHistoryAmount:
		del searchHistory[-1]

	try:
		file = open(PROFILE + category + '.txt', 'wb')
		pickle.dump(searchHistory, file)
		file.close()
	except:
		pass

def doSearch(category, scope=""):
	liz=xbmcgui.ListItem("New Search", iconImage="DefaultFolder.png")
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=base_url + '?mode=searchInput&category=' + category + '&scope=' + scope,listitem=liz,isFolder=True)
	searchHistory = getSearchHistory(category)
		
	for item in searchHistory:
		liz=xbmcgui.ListItem(item, iconImage="DefaultFolder.png")
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=base_url + '?mode=search&category=' + category + '&page=0&query=' + item + '&scope=' + scope,listitem=liz,isFolder=True)

def addStreamer(streamer):
	name = streamer["token"]
	id = str(streamer["id"]) or ""
	title = streamer["name"] or ""
	try:
		game = streamer["type"]["name"] or ""
	except:
		game = ""
	try:
		thumbnail = streamer["type"]["coverUrl"] or ""
	except:
		thumbnail = ""
	try:
		description = streamer["type"]["description"] or ""
	except:
		description = ""
	currentViewers = str(streamer["viewersCurrent"]) or ""
	
	u=base_url+"?broadcastID="+urllib.quote_plus(id)+"&mode=playStream&name="+urllib.quote_plus(name)+"&thumbnail="+urllib.quote_plus(thumbnail)
	
	liz=xbmcgui.ListItem(name + ' - ' + title, iconImage="DefaultVideo.png", thumbnailImage=thumbnail)
	if "bannerUrl" in streamer:
		liz.setArt({'fanart': streamer["bannerUrl"]})
	else:
		liz.setArt({'fanart': streamer["type"]["backgroundUrl"]})
	liz.setInfo( type="Video", infoLabels={ "Title": name + ' - ' + title, "Plot": 'Viewers: ' + currentViewers + '\n' + game + '\n' + description } )
	return xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz)



def addDir(name,url,mode,iconimage,args = None):
	u=sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&name="+urllib.quote_plus(name)
	if args:
		for arg in args:
			u = u + '&' + arg + '=' + urllib.quote_plus(args[arg])
	ok=True
	liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name } )
	ok=xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=True)
	return ok

def paginate(url, start):
	urlP = url + "?page=" + str(start) + "&language=en"
	xbmcplugin.setContent(addon_handle, 'videos')
	TOPSTREAMS(urlP)
	liz=xbmcgui.ListItem("Next Page", iconImage="DefaultFolder.png")
	#liz.setInfo( type="Video", infoLabels={ "Title": name } )
	xbmcplugin.addDirectoryItem(handle=addon_handle, url=base_url + '?mode=topstreams&page=' + str(int(start) + 1),listitem=liz,isFolder=True)

def searchChannels(query, start, scope):
	limit = 32
	#https://mixer.com/api/v1/channels?where=suspended:eq:0,languageId:ne:en&limit=32&page=0&order=partnered:desc,featureLevel:desc,online:desc,viewersCurrent:desc,viewersTotal:desc&noCount=1&scope=names&q=mario
	url = 'https://mixer.com/api/v1/channels?where=suspended:eq:0,online:eq:1&limit=' + str(limit) + '&page=' + str(start) + '&order=online:desc,viewersCurrent:desc,partnered:desc,featureLevel:desc,viewersTotal:desc&noCount=1&scope=' + scope + '&q=' + urllib.quote_plus(query)
	xbmcplugin.setContent(addon_handle, 'videos')
	req = urllib2.Request(url)
	req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0')
	response = urllib2.urlopen(req)
	link=response.read()
	response.close()
	data = json.loads(link)
	count = 0
	for streamer in data:
		count = count + 1
		addStreamer(streamer)
	
	if count >= limit:
		liz=xbmcgui.ListItem("Next Page", iconImage="DefaultFolder.png")
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=base_url + '?mode=search&category=channels&page=' + str(int(start) + 1) + '&scope=' + scope + '&query=' + query,listitem=liz,isFolder=True)

def searchGames(url, query, start):
	limit = 32
	urlP = url + "&limit=" + str(limit) + "&page=" + str(start) + "&query=" + urllib.quote_plus(query)
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
		try:
			thumbnail = game["coverUrl"] or ""
		except:
			thumbnail = ""
		try:
			backgroundArt = game["backgroundUrl"] or ""
		except:
			backgroundArt = ""
		try:
			title = game["name"] or ""
		except:
			title = ""
		try:
			currentViewers = str(game["viewersCurrent"]) or ""
		except:
			currentViewers = "N/A"
		u=base_url+"?gameID="+urllib.quote_plus(gameID)+"&mode=game&thumbnail="+urllib.quote_plus(thumbnail)
		liz=xbmcgui.ListItem(title, iconImage="DefaultVideo.png", thumbnailImage=game["coverUrl"])
		liz.setArt({'fanart': backgroundArt})
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
	name = data['name'] or ""
	gameDescription = data['type']['description'] or "" # Add error handling for missing key
	partnered = data['partnered'] and "True" or "False"
	viewersCurrent = str(data['viewersCurrent'] or "")
	audience = data['audience'] or ""
	fullDescription = name + '\n' + 'Partnered: ' + partnered + '\n' + 'Viewers: ' + viewersCurrent + '\n' + 'Audience: ' + audience + '\n' + gameDescription
	li.setInfo(type="Video", infoLabels={"Title":data['token'] + ' - ' + name + ' - ' + viewersCurrent, "Plot": fullDescription})
	
	return li

def selectPreferredOrLowerQuality(qualities):
	if playbackQuality in qualities:
		return qualities[playbackQuality]
	
	currentQuality = 0
	for quality in qualities:
		if currentQuality < quality <= playbackQuality:
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
		qualityName = int("".join(i for i in quality[2] if i.isdigit()))
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
	if mode[0] == "playStream":
		broadcastID = args.get('broadcastID', [None])
		thumbnail = args.get('thumbnail', [None])
		fetchManifest(broadcastID[0], thumbnail[0])
	if mode[0] == 'search':
		category = args.get('category', None)
		page = args.get('page', None)
		query = args.get('query', None)
		scope = args.get('scope', None)
		if not scope:
			scope = ""
		else:
			scope = scope[0]
		if page and query:
			if category and category[0] == 'games':
				searchGames("https://mixer.com/api/v1/types?order=viewersCurrent:desc&noCount=1", query[0], page[0])
			elif category and category[0] == 'channels':
				searchChannels(query[0], page[0], scope)
		elif category:
			doSearch(category[0], scope)
		else:
			SEARCH()
	if mode[0] == 'searchInput':
		category = args.get('category', None)
		scope = args.get('scope', None)
		if not scope:
			scope = ""
		else:
			scope = scope[0]
		query = getUserInput('Search')

		if query:
			if category:
				addToSearchHistory(category[0], query)
				if category[0] == 'games':
					searchGames("https://mixer.com/api/v1/types?order=viewersCurrent:desc&noCount=1", query, 0)
				elif category[0] == 'channels':
					searchChannels(query, 0, scope)
		else:
			SEARCH()

xbmcplugin.endOfDirectory(addon_handle)
