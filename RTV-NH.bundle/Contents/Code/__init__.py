# -*- coding: utf-8 -*-
import re, urllib2, os
from string import ascii_uppercase
from BeautifulSoup import BeautifulSoup
import urllib
from urllib2 import HTTPError
import httplib


PLUGIN_TITLE   = 'RTV NH gemist'

ART            = 'art-rtvnh.jpg'
ICON           = 'icon-default.png'
ICON_SEARCH    = 'icon-search.png'
ICON_PREFS     = 'icon-prefs.png'

base	= 'http://www.rtvnh.nl'
uzgurl	= base + '/uitzending-gemist'
streamerbase = 'rtmp://stream.rtvnh.nl/vod'
art		= 'art-rtvnh.png',
icon	= 'icon-rtvnh.png'


###################################################################################################
def Start():
	Plugin.AddPrefixHandler('/video/rtvnhgemist', MainMenu, PLUGIN_TITLE, ICON, ART)
	Plugin.AddViewGroup('List', viewMode='List', mediaType='items')
	Plugin.AddViewGroup('InfoList', viewMode='InfoList', mediaType='items')
  
	MediaContainer.title1 = PLUGIN_TITLE
	MediaContainer.viewGroup = 'InfoList'
	MediaContainer.art = R(ART)
  
	DirectoryItem.thumb = R(ICON)
	WebVideoItem.thumb = R(ICON)
	VideoItem.thumb = R(ICON)

	HTTP.CacheTime = 300
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:5.0) Gecko/20100101 Firefox/5.0'

###################################################################################################
def MainMenu():
# TODO add more choises besides days also programma keuze bijv.
	dir = MediaContainer()
	dir.Append(Function(DirectoryItem(getpas7days, title='Afelopen 7 dagen'), title='Afgelopen 7 dagen'))
	#dir.Append(Function(DirectoryItem(Episode, title='Programma keuze'), title='Programma keuze'))

	return dir

####################################################################################################
def getpas7days(sender, title):
	dir = MediaContainer(viewGroup='List', title2=sender.itemTitle)
			
	for day in HTML.ElementFromURL(uzgurl).xpath('//select[@name="program_date"]/option'):
		title = re.sub('\s+', ' ', day.text)
		date = day.get('value')
		if title == ' - maak een keuze - ' or title == 'specifieke periode...':
			continue
		
		dir.Append(Function(DirectoryItem(BrowseByDay, title=title), date=date))
  
	return dir
	
###################################################################################################
def BrowseByDay(sender, date):
	dir = MediaContainer(title='programma overzicht')
	
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0)')]
	params = urllib.urlencode({'program_date': date})
	#sectionnum = "1"
	#a = "/Applications/Plex\ Media\ Server.app/Contents/MacOS/Plex\ Media\ Scanner -t -c %s | grep -Ev '    ' | sed '/Season/d' | sed '/Specials/d' | cut -f1 -d'['" % sectionnum
	#p  = os.popen(a)
	#s = p.readlines()
	#p.close()
	try:
		infile = opener.open(uzgurl, params)
	except HTTPError, e:
		Log.Debug('e')
		data = ""
	else:
		data = infile.read()
	
	soup = BeautifulSoup(data, convertEntities=BeautifulSoup.HTML_ENTITIES, smartQuotesTo="xml")	
	videos = soup.findAll('div', {'class' : 'info-text'})
	
	for video in videos:
		label = video.h3.a.contents[0]
		label = label.strip()
		link = base + video.h3.a['href']
		clip = getflash(sender, link=link)
		image = getimage(sender, link=link)
		image = base + image
		dir.Append(Function(VideoItem(PlayVideo, title=label, thumb=Function(Thumb, url=image)), clip=clip))

	return dir

###################################################################################################
def getflash(sender, link):
# TODO FIX fix regexp to see if we don't need to strip
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0)')]
	#sectionnum = "1"
	#a = "/Applications/Plex\ Media\ Server.app/Contents/MacOS/Plex\ Media\ Scanner -t -c %s | grep -Ev '    ' | sed '/Season/d' | sed '/Specials/d' | cut -f1 -d'['" % sectionnum
	#p  = os.popen(a)
	#s = p.readlines()
	#p.close()
	try:
		infile = opener.open(link)
	except HTTPError, e:
		Log.Debug('e')
		data = ""
	else:
		data = infile.read()
	
	pattern_clip = ": '(.*?)\.mp4',"
	clip = re.findall(pattern_clip, data)
	clip = str(clip).strip('[\'\']')
	return clip

###################################################################################################
def getimage(sender, link):
# TODO FIX image regexp so i don't need to strip and add .jpg
	opener = urllib2.build_opener()
	opener.addheaders = [('User-agent', 'Mozilla/5.0)')]
	sectionnum = "1"
	a = "/Applications/Plex\ Media\ Server.app/Contents/MacOS/Plex\ Media\ Scanner -t -c %s | grep -Ev '    ' | sed '/Season/d' | sed '/Specials/d' | cut -f1 -d'['" % sectionnum
	p  = os.popen(a)
	s = p.readlines()
	p.close()
	try:
		infile = opener.open(link)
	except HTTPError, e:
		Log.Debug('e')
		data = ""
	else:
		data = infile.read()
	
	pattern_image = "'image': '(.*?)\.jpg',"
	image = re.findall(pattern_image, data)
	image = str(image).strip('[\'\']')
	image = image + '.jpg'
	return image
	
###################################################################################################
def PlayVideo(sender, clip):
	playclip = 'mp4:' + clip
	
	return Redirect(RTMPVideoURL(streamerbase, playclip))
	
###################################################################################################
def Thumb(url):
	try:
		data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
		return DataObject(data, 'image/jpeg')
	except:
		return Redirect(R(ICON))