
# import base64
# import datetime
# import json
import re
import requests
import sys
import xbmcaddon
import xbmcgui
import xbmcplugin

# py_2x_3x
import html
import urllib.error
import urllib.parse
import urllib.request

# py_2x_3x
# import HTMLParser
# from six.moves import urllib

# py_2x_3x
__settings__ = xbmcaddon.Addon(id="plugin.video.tang3")
# __settings__ = xbmcaddon.Addon(id="plugin.video.tang2")

BASE_URL = __settings__.getSetting("base_url")
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36"

# Get the plugin url in plugin:// notation.
PLUGIN_URL = sys.argv[0]
# Get a plugin handle as an integer number.
HANDLE = int(sys.argv[1])
args = urllib.parse.parse_qs(sys.argv[2][1:])

def addLog(message, level="notice"):
    if level == "error":
        xbmc.log(str(message), level=xbmc.LOGERROR)
    else:
        xbmc.log(str(message), level=xbmc.LOGINFO)

def addDir(name, url, mode, image, description="", isplayable=False):
    u = (
        PLUGIN_URL
        + "?url="
        + urllib.parse.quote_plus(url)
        + "&mode="
        + urllib.parse.quote_plus(mode)
        + "&name="
        + urllib.parse.quote_plus(name)
    )

    listitem = xbmcgui.ListItem(name)
    thumbnailImage = image
    listitem.setArt({"icon": "DefaultFolder.png", "thumb": thumbnailImage})
    listitem.setInfo(type="Video", infoLabels={"Title": name, "Plot": description})
    listitem.setProperty("IsPlayable", "true")
    isfolder = True
    if isplayable:
        isfolder = False
    ok = xbmcplugin.addDirectoryItem(
        handle=int(sys.argv[1]), url=u, listitem=listitem, isFolder=isfolder
    )
    return ok

def select_menu():
    addLog("BASE_URL: " + BASE_URL)
    addDir(
        "HD Movies",
        BASE_URL + "/video-category/hd-movies/",
        "listing",
        "DefaultAddonsRecentlyUpdated.png",
    )
    addDir(
        "Web Series",
        BASE_URL + "/video-category/web-series/",
        "listing",
        "DefaultMovies.png",
    )
    addDir(
        "Trending Movies",
        BASE_URL + "/trending/",
        "listing",
        "DefaultRecentlyAddedMovies.png",
    )
    addDir(
        "Dubbed Movies",
        BASE_URL + "/video-category/dubbed-movies/",
        "listing",
        "DefaultDirector.png",
    )
    addDir(
        "Search",
        BASE_URL + "/",
        "search",
        "DefaultAddonsSearch.png",
    )
    addDir("Addon Settings", "", "addon_setttings", "DefaultAddonService.png", "")
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def select_settings():
    __settings__.openSettings()


def menu_search(name, url, mode):
    keyb = xbmc.Keyboard("", "Search")
    keyb.doModal()
    if keyb.isConfirmed():
        search_term = urllib.parse.quote_plus(keyb.getText())
        postData = url + "&query=" + str(search_term)
        browse_results(name, postData, mode)


def browse_home(name, url, mode):
    addLog("browse_home: " + url)
    list_videos(url, "home")


def browse_results(name, url, mode):
    addLog("browse_results: " + url)
    list_videos(url, "results")


def list_videos(url, pattern):
    video_list = scrape_videos(url, pattern)
    # [(movie_url, title, description, next_page)]
    # TODO: what if the list is empty?

    for video_item in video_list:
        movie_url, title, description, next_page = video_item
        addDir(
            title,
            movie_url,
            "play",
            "DefaultMovies.png",
            description,
            isplayable=True,
        )

    if video_list[-1][-1] != "":
        addDir(">>> Next Page >>>", BASE_URL + video_list[-1][-1], "listing", "")

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def scrape_videos(url, pattern):
    html1 = requests.get(url).text
    results = []
    next_page = ""
    regexstr = 'class="post-listing-title".+?href="(.+?)".+?title="(.+?)".+?>(.+?)<\/a>'
    video_matches = re.findall(regexstr, html1)
    nextpage_regexstr = 'class="nextpostslink".+?href="(.+?)">'
    next_matches = re.findall(nextpage_regexstr, html1)
    if len(next_matches) > 0:
        next_page = next_matches[-1][0]
    refererurl = url
    for item in video_matches:
        movie_url = item[0]
        movie_title = item[1].encode("ascii", "ignore").decode("ascii")
        movie_description = item[2].encode("ascii", "ignore").decode("ascii")
        results.append(
            (
                str(movie_url),
                str(movie_title),
                str(movie_description),
                str(refererurl),
                str(next_page),
            )
        )
    return results


def play_video(name, url, mode, refurl):
    # RETRY_BACKUP = __settings__.getSetting("retry_backup")
    # addLog("retry_backup: " + RETRY_BACKUP)

    addLog("play_video: " + url)

    s = requests.Session()

    # lang, movieid, moviename, hdtype, refurl = url.split(",")
    # if RETRY_BACKUP == "true":
    #     try_second urlStream

    result = get_video(s, name, url, refurl)

    if result == False:
        return False

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def get_video(s, name, videourl, refererurl):
    addLog("get_video: " + str(videourl))

    headers = {
        "Origin": BASE_URL,
        "Referer": refererurl,
        "User-Agent": USER_AGENT,
    }

    html1 = s.get(videourl, headers=headers, cookies=s.cookies).text

    csrf1 = re.findall('"video_url":".+?src=(.*?) title', html1)
    if len(csrf1) == 0:
        addLog("Video URL not found", "error")
        xbmcgui.Dialog().ok(
            "Video URL not found",
            "Video URL not found. Please report this issue to the developer.",
        )
        return False
    csrf1 = csrf1[0].decode('string_escape')
    # py_2x_3x
    csrf1 = html.unescape(csrf1)
    # csrf1 = HTMLParser.HTMLParser().unescape(csrf1).encode("utf-8")
    player_url = csrf1

    addLog("get_player: " + str(player_url))
    html2 = s.get(player_url, headers=headers, cookies=s.cookies).text
    streamURLs = re.findall('"urlStream":"(.*?)","type"', html2)
    if len(streamURLs) == 0:
        addLog("urlStream not found", "error")
        xbmcgui.Dialog().ok(
            "urlStream not found",
            "urlStream not found. Please report this issue to the developer.",
        )
        return False
    url1 = streamURLs[0]
    url2 = url1 + ("|%s&Referer=%s&User-Agent=%s" % (BASE_URL, player_url, USER_AGENT))
    addLog("url2: " + url2)
    listitem = xbmcgui.ListItem(name)
    thumbnailImage = xbmc.getInfoImage("ListItem.Thumb")
    listitem.setArt({"icon": "DefaultVideo.png", "thumb": thumbnailImage})
    listitem.setProperty("IsPlayable", "true")
    listitem.setPath(url2)
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, listitem)

    s.close()
    return True


# try:
#     description = urllib.parse.unquote_plus(params["description"])
# except:
#     pass
url=""
mode="menu"
name="Home"

def router():
    params = dict(args)

    try:
        url = urllib.parse.unquote_plus(params["url"])
    except:
        pass
    try:
        mode = urllib.parse.unquote_plus(params["mode"])
    except:
        pass
    try:
        name = urllib.parse.unquote_plus(params["name"])
    except:
        pass

    if params:
        if params['mode'][0] == 'listing':
            list_videos(url, name)
        elif params['mode'][0] == 'search':
            menu_search(name, url, mode)
        elif params['mode'][0] == 'menu':
            select_menu()
        elif params['mode'][0] == 'settings':
            select_settings()
        elif params['mode'][0] == 'play':
            play_video(name, url, mode, BASE_URL)
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(params))
    else:
        select_menu()
        # list_folders()


router()