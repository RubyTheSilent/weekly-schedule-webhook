import re
import json
import threading
import traceback

from os import path

import requests
import datetime

config = {}
with open("config.json","r") as fp:
    config = json.load(fp)
base     = "https://canary.discord.com/api/webhooks/"
id_wh    = config.get("id")
token_wh = config.get("token")
phrase   = config.get("phrase")
description = config.get("description")
youtube_url_community = config.get("youtube_url")
def parse_yt_post_url(url)->str:
    regex_str = '("postId":)"(.*?)","authorText":{"runs":\[{"text":".*?","navigationEndpoint":{"clickTrackingParams":".*?","commandMetadata":{"webCommandMetadata":{"url":"/.*?","webPageType":".*?","rootVe":[0-9]+,"apiUrl":"/youtubei/v[0-9]+/browse"}},"browseEndpoint":{"browseId":".*?","canonicalBaseUrl":".*?"}}}\],"accessibility":{"accessibilityData":{"label":".*?"}}},"authorThumbnail":{"thumbnails":\[{"url":"//yt3.googleusercontent.com/.*?-c-k-c0x00ffffff-no-rj-mo","width":[0-9]+,"height":[0-9]+},{"url":"//yt3.googleusercontent.com/.*?-c-k-c0x00ffffff-no-rj-mo","width":[0-9]+,"height":[0-9]+},{"url":"//yt3.googleusercontent.com/.*?-c-k-c0x00ffffff-no-rj-mo","width":[0-9]+,"height":[0-9]+}],"accessibility":{"accessibilityData":{"label":".*?"}}},"authorEndpoint":{"clickTrackingParams":".*?","commandMetadata":{"webCommandMetadata":{"url":".*?","webPageType":".*?","rootVe":[0-9]+,"apiUrl":"/youtubei/v[0-9]+/browse"}},"browseEndpoint":{"browseId":".*?","canonicalBaseUrl":".*?"}},"contentText":{"runs":\[{"text":(".*?")}'
    try:
        resp = requests.get(url)
        g = re.findall(regex_str,resp.text)
        baseurl = "https://www.youtube.com/post/"
        ids = "Not Found"
        for found in g:
            if found[2] == phrase:
                ids = found[1]
                break
        posturl = baseurl + ids
        if ids != "Not Found":
            return posturl
        return "Not Found"
    except re.error as e:
        err_str = f"REGEX: ERROR At Regex Pattern Character at {str(e)[len(str(e))-2:]}({regex_str[int(str(e)[len(str(e))-2:])]})"
        print(err_str, end="\r")
        return err_str
def parse_yt_post_attachment(post_url):
    #https://yt3.ggpht.com/BPFNfTj4eN5Upt6NKPj08tY5SMVUZhrqxKBI7sUcz99FdOlop0BrL1vh6yoODL3KVSmcw0Ndxlz-COQ=s640-nd-v1
    #https://yt3.ggpht.com/MmrfOl4z-N3Ep80Yhv8bT7CK7KKo6zutSEdEovalkeRKQ0VU8Vad0uQHjd175fiwL3PYBdfueLDt1Q=s640-nd-v1
    regex_str = "https:\/\/yt3\.ggpht\.com\/(.{83}|.{82}|.{81}|.{80}|.{79}|.{78}|.{77}|.{76}|.{75}|.{74})=s[0-9]+-nd-v[0-9]+"
    try:
        resp = requests.get(post_url)
        g = re.findall(regex_str,resp.text)
        if len(g) > 0:
            #print(g[0])
            return "https://yt3.ggpht.com/"+g[0]+"=s640-nd-v1"
        return "Not Found"
    except re.error as e:
        err_str = f"REGEX: ERROR At Regex Pattern Character at {str(e)[len(str(e))-2:]}({regex_str[int(str(e)[len(str(e))-2:])]})"
        print(err_str, end="\r")
        return err_str

def update_loop():
    global Stop
    global last_update
    global post_url
    while not Stop:
        try:
            if datetime.datetime.utcnow() > last_update :
                last_update = datetime.datetime.utcnow() + datetime.timedelta(seconds=int((5*60)))
                new_post_url = parse_yt_post_url(youtube_url_community)
                if new_post_url != "Not Found" and post_url != new_post_url:
                    post_url = new_post_url
                    url_img = parse_yt_post_attachment(new_post_url)
                    if url_img[:5] == "REGEX" or url_img == "Not Found":
                        print("Image", url_img, end="\r")
                    else:
                        json_data = {
                            "content" : datetime.datetime.today().strftime(r'%Y-%m-%d')+f"\n{post_url}",
                            "username" : "post ตารางไลฟ์",
                            "tts" : False,
                            "allowed_mentions" : False,
                            "embeds" : [
                                {
                                    "url" : post_url,
                                    "title" : phrase,
                                    "type" : "rich",
                                    "description" : "แล้วเจอนะคะ!!! (ᗒᗨᗕ) ✨",
                                    "footer" : {
                                        "text":"*ตารางอาจมีการเปลี่ยนแปลง ขออภัยในความไม่สะดวกค่ะ*"
                                    },
                                    "color" : 8432738,
                                    "image" : {
                                        "url" : url_img
                                    }
                                }
                            ]
                        }
                        resp = requests.post(base + "/" + id_wh + "/" + token_wh, json=json_data)
                        if resp.status_code in range(200,400):
                            print("Ok")
                        else:
                            print(resp.status_code)
                else:
                    print("Old One", end="\r")
        except:
            traceback.print_exc()
if __name__ == "__main__":
    Stop = False
    try:
        last_update = datetime.datetime.utcnow() + datetime.timedelta(seconds=int((5*60)))
        post_url = ""
        
        if not path.exists("last_update.json"):
            with open("last_update.json","w") as fp:
                json.dump({"url":"","last_update_iso":datetime.datetime.utcnow().isoformat()},fp)

        with open("last_update.json","r") as fp:
            json_save = json.load(fp)
            last_update = datetime.datetime.fromisoformat(json_save["last_update_iso"])
            post_url = json_save["url"]

        webhook_update_thread = threading.Thread(target=update_loop)
        webhook_update_thread.daemon = True
        webhook_update_thread.start()
        last_auto_save = datetime.datetime.utcnow() + datetime.timedelta(seconds=60)

        while True:
            try:
                if datetime.datetime.utcnow() > last_auto_save:
                    last_auto_save = datetime.datetime.utcnow() + datetime.timedelta(seconds=60)
                    with open("last_update.json","w") as fp:
                        json.dump({"url":post_url,"last_update_iso":last_update.isoformat()},fp)

            except KeyboardInterrupt:
                Stop = True
                break
        with open("last_update.json","w") as fp:
            json.dump({"url":post_url,"last_update_iso":last_update.isoformat()},fp)
    except:
        traceback.print_exc()
        Stop = True
