# -*- coding: utf-8 -*-
import re, os
from string import ascii_uppercase


PLUGIN_TITLE   = 'RTV NH gemist'

ART            = 'art-rtvnh.jpg'
ICON           = 'icon-default.png'
ICON_SEARCH    = 'icon-search.png'
ICON_PREFS     = 'icon-prefs.png'

base	= 'http://www.rtvnh.nl'
uzgurl	= base + '/uitzending-gemist'
streamerbase = 'rtmp://stream.rtvnh.nl/vod/'
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
	
	result = {}

	params = {'program_date': date}
	@parallelize
	def GetVideos():

		html = HTML.ElementFromURL(uzgurl, values=params)
		videos = html.xpath('//div[starts-with(@class, "info-text")]')
		
		for num in range(len(videos)):
			video = videos[num]
			
			@task
			def GetVideo(num = num, result = result, video = video):
				try:
					video_url = video.xpath('./h3/a')[0].get('href')
					label = video.xpath('./h3/a')[0].text
					label = label.strip()
					clip = getflash(sender, link=video_url)
					image = getimage(sender, link=video_url)
					image = base + image
					result[num] = VideoItem(Function(PlayVideo, title=label, clip=clip), title=label, thumb=Function(Thumb, url=image), clip=clip)
				except:
					Log("Couldn't add clip from %s" % video_url)
					pass
	
	keys = result.keys()
	keys.sort()
  
	for key in keys:
		dir.Append(result[key])
		
	return dir

###################################################################################################
def getflash(sender, link):
# TODO FIX fix regexp to see if we don't need to [0]
	link = base + link
	content = HTTP.Request(link, cacheTime=0).content
	clip = re.compile(': \'(.*?)\.mp4\',').findall(content, re.DOTALL)
	clip = str(clip[0])
	return clip

###################################################################################################
def getimage(sender, link):
## TODO FIX image regexp so i don't need to strip and add .jpg
	link = base + link
	content = HTTP.Request(link, cacheTime=0).content
	image = re.compile(': \'(.*?)\.jpg\',').findall(content, re.DOTALL)
	image = str(image[0])
	image = image + '.jpg'
	return image
	
###################################################################################################
def PlayVideo(sender, title, clip):
	playclip = 'mp4:' + clip
	
	return Redirect(RTMPVideoURL(streamerbase, playclip))
	
###################################################################################################
def Thumb(url):
	try:
		data = HTTP.Request(url, cacheTime=CACHE_1WEEK).content
		return DataObject(data, 'image/jpeg')
	except:
		return Redirect(R(ICON))