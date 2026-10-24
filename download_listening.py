"""Download the selected public INLL podcast originals for personal listening.

Run with .venv/bin/python download_listening.py. No notes or recordings are uploaded.
The catalog contains source links and original practice, not publisher transcripts.
"""
from datetime import timezone
from email.utils import parsedate_to_datetime
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse, unquote
import xml.etree.ElementTree as ET

import httpx

ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "listening_catalog.json"
CACHE = ROOT / ".cache/listening"
LIMIT = 40 * 1024 * 1024


def main():
    catalog = json.loads(CATALOG.read_text())
    CACHE.mkdir(parents=True, exist_ok=True)
    with httpx.Client(follow_redirects=True, timeout=60) as client:
        response = client.get(catalog["rss_url"])
        response.raise_for_status()
        items = {item.findtext("title"): item for item in ET.fromstring(response.content).findall("channel/item")}
        for episode in catalog["episodes"]:
            item = items[episode["publisher_title"]]
            url = item.find("enclosure").get("url")
            if urlparse(url).scheme != "https" or urlparse(url).hostname != "anchor.fm":
                raise ValueError("Unexpected publisher audio host")
            suffix = ".m4a" if unquote(url).endswith(".m4a") else ".mp3"
            target = CACHE / (episode["id"] + suffix)
            episode.update(audio_file=target.name, audio_url=url, publisher_url=item.findtext("link"),
                           transcript_url=item.findtext("link"),
                           published=parsedate_to_datetime(item.findtext("pubDate")).astimezone(timezone.utc).date().isoformat(),
                           duration=item.findtext("{http://www.itunes.com/dtds/podcast-1.0.dtd}duration"))
            if not target.is_file():
                partial = target.with_suffix(suffix + ".part")
                try:
                    with client.stream("GET", url) as audio, partial.open("wb") as output:
                        audio.raise_for_status()
                        content_type = audio.headers.get("content-type", "").split(";")[0]
                        if content_type not in {"audio/mpeg", "audio/mp4", "audio/x-m4a", "application/octet-stream"}:
                            raise ValueError("Publisher returned something other than audio")
                        size = 0
                        for chunk in audio.iter_bytes():
                            size += len(chunk)
                            if size > LIMIT:
                                raise ValueError("Unexpectedly large episode")
                            output.write(chunk)
                    if size < 1024:
                        raise ValueError("Audio download is incomplete")
                    partial.replace(target)
                finally:
                    partial.unlink(missing_ok=True)
            episode["audio_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
            print(f"Ready: {episode['title']} ({episode['duration']})", flush=True)
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
