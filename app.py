#!/usr/bin/python3

import requests, os, sys, json, math, argparse, youtube_dl, re
from requests import Session, Request
from pathlib import Path
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

parser = argparse.ArgumentParser(description="download streamable videos and optionally upload to gdrive")
parser.add_argument("session_id", metavar="Streamable Session ID", type=str, help="your streamable.com session value")
parser.add_argument("username", metavar="Streamable Username", type=str, help="your streamable.com user_name value")
parser.add_argument("usercode", metavar="Streamable Usercode", type=str, help="your streamable.com user_code value")
parser.add_argument("--gdrive", action='store_true')
parser.add_argument("--replace_spaces", metavar="Replaces whitespace in filenames with _underscores_")

replace = re.compile(r"[\\/:\"*?<>|]")
args = parser.parse_args()
cwd = os.getcwd()
videos_directory = cwd + "\\videos"
Path(videos_directory).mkdir(parents=True, exist_ok=True)
ydl = youtube_dl.YoutubeDL({"outtmpl": videos_directory + "\\%(id)s.%(ext)s"})
base_url = "https://ajax.streamable.com/videos?count=100&page="
g_login = GoogleAuth()
drive = GoogleDrive()
g_drive_folder = "streamable-videos"

if args.gdrive:
    if os.name != "nt":
        g_login.CommandLineAuth()
    else:
        print("Unfortunately, you are running on Windows, so invalid NTFS filename characters will be replaced with nothing. For example, a video with the title \"Are you for real?\" will be saved with the filename: \"Are you for real.mp4\".")
        g_login.LocalWebserverAuth()
    drive = GoogleDrive(g_login)

session = requests.session()
cookie = requests.cookies.create_cookie(domain=".streamable.com", name="session", value=args.session_id)
session.cookies.set_cookie(cookie)
cookie = requests.cookies.create_cookie(domain=".streamable.com", name="user_name", value=args.username) 
session.cookies.set_cookie(cookie)
cookie = requests.cookies.create_cookie(domain=".streamable.com", name="user_code", value=args.usercode)
session.cookies.set_cookie(cookie)

request = session.get("https://ajax.streamable.com/videos")

data = []

if request.status_code == 200:
    video_count = request.json()["total"]
    pages_to_enumerate = math.ceil(video_count / 100)
    prepared_requests = [Request("GET", base_url + str(page_number)).prepare() for page_number in range(1, pages_to_enumerate + 1)]
    page_video_count = 0
    for prepared_request in prepared_requests:
        prepared_request.prepare_cookies(session.cookies)
        request = session.send(prepared_request)
        if request.status_code == 200:
            videos = request.json()["videos"]
            page_video_count += len(request.json()["videos"])
            for video in videos:
                title = video["title"].replace(" ", "_") if args.replace_spaces else video["title"]
                title = replace.sub('', title) if os.name == "nt" else title
                data.append({"filename": video["shortcode"] + "_" + title + "." + video["ext"], "shortcode": video["shortcode"], "title": video["title"], "location_on_disk": videos_directory + "\\" + video["shortcode"] + "." + video["ext"], "json": video})

    folders = drive.ListFile({"q": "mimeType=\"application/vnd.google-apps.folder\" and trashed=false"}).GetList()
    folder_id = None

    for folder in folders:
        if folder["title"] == g_drive_folder:
            folder_id = folder["id"]

    if folder_id is None:
        folder = drive.CreateFile({"title": "streamable-videos", "mimeType": "application/vnd.google-apps.folder"})
        folder.Upload()
        folder_id = folder["id"]

    os.chdir(videos_directory)

    for video in data:
        if not os.path.isfile(video["location_on_disk"]) and not os.path.isfile(videos_directory + "\\" + video["filename"]):
            ydl.download([video["json"]["url"]])
            os.rename(video["location_on_disk"], videos_directory + "\\" + video["filename"])
        elif os.path.isfile(video["location_on_disk"]) and not os.path.isfile(videos_directory + "\\" + video["filename"]):
            os.rename(video["location_on_disk"], videos_directory + "\\" + video["filename"])
        video_gdrive_file = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": folder_id}]})
        video_gdrive_file.SetContentFile(video["filename"])
        video_gdrive_file.Upload()

    print("Downloaded all videos") if video_count == page_video_count else print("Failed to download all videos, downloaded {0} videos out of {1} videos".format(page_video_count, video_count))

    with open("data.json", "w") as json_file:
        json_file.write(json.dumps(data, indent=4))

    video_gdrive_file = drive.CreateFile({"parents": [{"kind": "drive#fileLink", "id": folder_id}]})
    video_gdrive_file.SetContentFile("data.json")
    video_gdrive_file.Upload()
else:
    sys.exit("Failed base request: {0}".format(request.status_code))