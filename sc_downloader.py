import os
import sys
import requests as rq
import shutil
import re
import json
import threading
import base64
import random
import time
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TPE1, error

CLIENT_ID = "2412b70da476791567d496f0f3c26b88"
APPENDUM = f"?client_id={CLIENT_ID}"

def rem_bad_chars(fname):
    for c in [ "<", ">", ":", "\"", "/", "\\", "|", "?", "*" ]:
        fname = fname.replace(c, " ")
    return fname

def extractValidUrl(url):
    rgx = re.search("^(http://|https://|)soundcloud.com/[a-zA-Z0-9][ A-Za-z0-9_-]*$", url)
    if rgx is not None:
        return rgx.group()
    return None

def request_api_data_json(url):
    r = rq.get(url)
    return json.loads(r.text)

def download_api_mp3(audio_url, art_url, artist, path, id):
    if os.path.exists(path):
        print("track already exists at the specified location on this machine.")
        sys.stdout.flush()
        return
    r = rq.get(audio_url, stream=True)
    try:
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        mp3 = MP3(path, ID3=ID3)
        try:
            mp3.add_tags()
        except error:
            pass
        if art_url is not None:
            art_url = "t500x500".join(art_url.rsplit("large", 1)) # get high resolution artwork instead of the shitty low res one sc wants you to have
            img_response = rq.get(art_url, stream=True)
            with open(f"temps/{id}/temp.jpg", "wb") as f:
                shutil.copyfileobj(img_response.raw, f)
            del img_response
            mp3.tags.add(APIC(mime="image/jpeg", type=3, desc=u"Cover", data=open(f"temps/{id}/temp.jpg", "rb").read()))
        mp3.tags.add(TPE1(encoding=3, text=f"{artist}"))
        mp3.save()
    except OSError as ose:
        if ose.errno == 36:
            mp3name = f"{os.path.basename(path)[0:50]}.mp3"
            download_api_mp3(audio_url, art_url, artist, path.replace(os.path.basename(path), mp3name), id)
    return

def download_playlists(folder_path, url_path, permalink):
    id = os.path.normpath(folder_path).split(os.path.sep)[1]
    os.mkdir(f"temps/{id}")
    profile_url = f"https://api.soundcloud.com/users/{permalink}{APPENDUM}"
    profile_id = request_api_data_json(profile_url)
    if "code" not in profile_id:
        profile_id = profile_id["id"]
        playlists_url = f"https://api.soundcloud.com/users/{profile_id}/playlists.json{APPENDUM}"
        playlist_json_list = request_api_data_json(playlists_url)
        if len(playlist_json_list) == 0:
            print("User has not created any playlists.")
            sys.stdout.flush()
            return False
        for playlist in playlist_json_list:
            playlist_title = rem_bad_chars(playlist["title"])
            for track in playlist["tracks"]:
                track_path = f"{folder_path}/{playlist_title}"
                if not os.path.isdir(track_path):
                    os.makedirs(track_path)
                if track["streamable"]:
                    artwork_url = track["artwork_url"]
                    print(f"Downloading {track['title']} by {track['user']['username']} in playlist {playlist['title']}...")
                    sys.stdout.flush()
                    track_name = rem_bad_chars(track["title"])
                    download_api_mp3(f"{track['stream_url']}{APPENDUM}", artwork_url if artwork_url else track["user"]["avatar_url"], track["user"]["username"], f"{track_path}/{track_name}.mp3", id)
        print("All playlists downloaded. Zipping them up...")
        sys.stdout.flush()
        shutil.rmtree(f"temps/{id}")
    else:
        print("Soundcloud user does not exist.")
        sys.stdout.flush()
        return False
    return True

def start(folder_path_entry, url_path_entry):
    folder_path = folder_path_entry if os.path.isdir(folder_path_entry) else None
    url_path = extractValidUrl(url_path_entry)

    if folder_path and url_path:
        permalink = url_path.split("/")[-1]
        success = download_playlists(folder_path, url_path, permalink)
        if success:
            shutil.make_archive(f"zips/{url_path_entry.rsplit('/')[-1]}", "zip", folder_path)
            print("Zip archive written. Now downloading...")
            sys.stdout.flush()
            time.sleep(0.005)
            print("Zip archive written.")
            sys.stdout.flush()
    else:
        print("Please enter a valid soundcloud user URL.")
        sys.stdout.flush()

def main(argv):
    if len(argv) == 1:
        dpath = f"./downloads/{base64.b16encode(random.getrandbits(128).to_bytes(16, byteorder='little'))}"
        dd = {ord(c):None for c in ['b', '\'']}
        dpath = dpath.translate(dd)
        if os.path.exists(dpath):
            print("Sorry, something went wrong. Please try again.")
            sys.stdout.flush()
        else:
            os.mkdir(dpath)
            start(dpath, argv[0])
            shutil.rmtree(dpath)

if __name__ == "__main__":
    main(sys.argv[1:])