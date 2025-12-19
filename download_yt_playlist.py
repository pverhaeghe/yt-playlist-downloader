from pathlib import Path

from yt_dlp import YoutubeDL
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from mutagen.mp3 import MP3

# Dossier de sortie (dans ton repo / Codespace)
BASE_OUTPUT_DIR = Path("YoutubePlaylists")


def download_playlist(playlist_url: str):
    BASE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "ignoreerrors": True,
        "quiet": False,
        "extract_flat": False,
        "format": "bestaudio/best",
        # dossier = titre de la playlist, fichier = titre de la vidéo
        "outtmpl": str(BASE_OUTPUT_DIR / "%(playlist_title)s" / "%(title)s.%(ext)s"),
        "postprocessors": [
            {  # conversion en mp3
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "writethumbnail": True,   # télécharge la miniature
        "embedthumbnail": False,  # on intègre la pochette nous-mêmes
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(playlist_url, download=True)
        if info is None:
            print("Impossible de récupérer la playlist.")
            return

        # playlist ou vidéo unique
        if info.get("_type") == "playlist":
            entries = info.get("entries", [])
        else:
            entries = [info]

    for entry in entries:
        if not entry:
            continue

        title = entry.get("title", "Sans_titre")
        uploader = entry.get("artist") or entry.get("uploader") or "Inconnu"
        album = info.get("title", "Playlist YouTube")

        playlist_title = info.get("title", "Playlist")
        playlist_dir = BASE_OUTPUT_DIR / playlist_title
        playlist_dir.mkdir(parents=True, exist_ok=True)

        # Fichier MP3 généré par yt-dlp
        audio_path = playlist_dir / f"{title}.mp3"
        if not audio_path.exists():
            # yt-dlp peut avoir modifié le nom (caractères spéciaux)
            candidates = list(playlist_dir.glob("*.mp3"))
            if len(candidates) == 1:
                audio_path = candidates[0]
            else:
                print(f"MP3 introuvable pour : {title}")
                continue

        # Miniature (pochette) possible : jpg / webp / png
        thumb = None
        for ext in ("jpg", "webp", "png"):
            candidate = playlist_dir / f"{title}.{ext}"
            if candidate.exists():
                thumb = candidate
                break

        # Intégration pochette + tags ID3
        try:
            audio = MP3(audio_path, ID3=ID3)
            try:
                audio.add_tags()
            except Exception:
                pass  # tags déjà présents

            if thumb and thumb.exists():
                with open(thumb, "rb") as img:
                    audio.tags.add(
                        APIC(
                            encoding=3,
                            mime="image/jpeg",
                            type=3,  # front cover
                            desc="Cover",
                            data=img.read(),
                        )
                    )

            audio.tags["TIT2"] = TIT2(encoding=3, text=title)
            audio.tags["TPE1"] = TPE1(encoding=3, text=uploader)
            audio.tags["TALB"] = TALB(encoding=3, text=album)

            audio.save()
        except Exception as e:
            print(f"Erreur tag/pochette pour {audio_path}: {e}")

    print("Téléchargement et traitement terminés.")


if __name__ == "__main__":
    url = input("Colle l'URL de la playlist YouTube / YouTube Music (interface web) : ").strip()
    if url:
        download_playlist(url)
    else:
        print("URL vide, arrêt.")
