# streamable-downloader
quick script to download all streamable videos on account and archive to gdrive

# arguments (--flags are optional)
  - `session_id`          your streamable session id
  - `username`            your streamable username
  - `usercode`            your streamable usercode
  - `--gdrive`            to upload to gdrive or not
  - `--replace_spaces`    to replace spaces in filenames with underscores or not
  
# how to get session_id, usercode
log into streamable, open console in firefox/chrome, go to network/requests tab, refresh videos page, find first request, copy cookies with relevant names.
  
# requirements
  - python3
    - requests
    - youtube_dl
    - pydrive
    
# setup
if you don't want to authorize gdrive using my gapps API key, you can generate that yourself. then replace the keys in `client_secrets.json`. follow [this](https://support.google.com/googleapi/answer/6158862?hl=en) to generate api keys.

# gdrive
a folder named `streamable-videos` is created on your gdrive, all videos are uploaded to this folder.
