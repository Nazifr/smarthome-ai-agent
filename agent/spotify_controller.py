"""
SpotifyController — Spotify Müzik Kontrolcüsü

Agent'ın müzik kararlarını gerçek Spotify çalmasına dönüştürür.
label_mapping.json'daki spotify:playlist:xxx URI'lerini kullanır.

Kurulum:
1. spotify_auth.py çalıştır → .spotify_cache oluşur
2. docker-compose.yml'e SPOTIFY_CLIENT_ID ve SPOTIFY_CLIENT_SECRET ekle
"""

import os
import json
import time

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    SPOTIPY_AVAILABLE = True
except ImportError:
    SPOTIPY_AVAILABLE = False

SPOTIFY_CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_REDIRECT_URI  = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
SPOTIFY_CACHE_PATH    = os.path.join(os.path.dirname(__file__), ".spotify_cache")

SCOPE = "user-modify-playback-state user-read-playback-state playlist-read-private"

# Mood-to-playlist mapping (override via env vars for custom playlists)
MOOD_PLAYLISTS: dict[str, str] = {
    "notr":    os.getenv("SPOTIFY_PLAYLIST_NOTR",    "spotify:playlist:37i9dQZF1DX4sWSpwq3LiO"),  # Peaceful Piano
    "yorgun":  os.getenv("SPOTIFY_PLAYLIST_YORGUN",  "spotify:playlist:37i9dQZF1DXd9nC7BoIDEL"),  # Sleep
    "aktif":   os.getenv("SPOTIFY_PLAYLIST_AKTIF",   "spotify:playlist:37i9dQZF1DX76Wlfdnj7AP"),  # Beast Mode
    "stresli": os.getenv("SPOTIFY_PLAYLIST_STRESLI", "spotify:playlist:37i9dQZF1DX1s9knjP51Oa"),  # Calm Vibes
}


class SpotifyController:
    def __init__(self):
        self.sp = None
        self._mood_play_time = 0.0
        self._last_command = None
        self._pause_failed = False
        self._init_spotify()

    def _init_spotify(self):
        if not SPOTIPY_AVAILABLE:
            print("[Spotify] ⚠️ spotipy yüklü değil")
            return
        if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
            print("[Spotify] ⚠️ API key'ler ayarlanmamış, Spotify devre dışı")
            return
        if not os.path.exists(SPOTIFY_CACHE_PATH):
            print("[Spotify] ⚠️ .spotify_cache bulunamadı — önce spotify_auth.py çalıştır")
            return
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=SPOTIFY_CLIENT_ID,
                client_secret=SPOTIFY_CLIENT_SECRET,
                redirect_uri=SPOTIFY_REDIRECT_URI,
                scope=SCOPE,
                cache_path=SPOTIFY_CACHE_PATH,
                open_browser=False
            ))
            user = self.sp.current_user()
            print(f"[Spotify] ✓ Bağlandı — Kullanıcı: {user['display_name']}")
        except Exception as e:
            print(f"[Spotify] Bağlantı hatası: {e}")
            self.sp = None

    def play(self, music_value: str):
        """
        music_value: spotify:playlist:xxx veya 'kapali'
        """
        if not self.sp:
            return
        if music_value == self._last_command:
            return
        self._last_command = music_value

        if music_value == "kapali":
            self._pause()
            return

        if music_value.startswith("spotify:playlist:"):
            self._play_playlist(music_value)
        else:
            print(f"[Spotify] Bilinmeyen müzik değeri: {music_value}")

    def _play_playlist(self, playlist_uri: str):
        try:
            # Aktif cihaz var mı kontrol et
            devices = self.sp.devices()
            active_devices = [d for d in devices.get("devices", []) if d["is_active"]]

            if not active_devices:
                # Aktif cihaz yoksa ilk cihazı kullan
                all_devices = devices.get("devices", [])
                if not all_devices:
                    print("[Spotify] ⚠️ Aktif Spotify cihazı bulunamadı. Telefon/bilgisayarda Spotify'ı aç.")
                    return
                device_id = all_devices[0]["id"]
                device_name = all_devices[0]["name"]
            else:
                device_id = active_devices[0]["id"]
                device_name = active_devices[0]["name"]

            self.sp.start_playback(
                device_id=device_id,
                context_uri=playlist_uri,
            )
            self._pause_failed = False
            print(f"[Spotify] ▶ Çalıyor: {playlist_uri} → {device_name}")

        except spotipy.exceptions.SpotifyException as e:
            if "Premium" in str(e):
                print("[Spotify] ⚠️ Spotify Premium gerekli")
            else:
                print(f"[Spotify] Çalma hatası: {e}")
        except Exception as e:
            print(f"[Spotify] Hata: {e}")

    def _pause(self):
        if time.time() - self._mood_play_time < 300:
            return
        if self._pause_failed:
            return
        try:
            self.sp.pause_playback()
            self._pause_failed = False
            print("[Spotify] ⏸ Müzik durduruldu")
        except Exception as e:
            if "403" in str(e) or "Restriction" in str(e):
                self._pause_failed = True
            else:
                print(f"[Spotify] Durdurma hatası: {e}")

    def play_for_mood(self, sentiment: str):
        """Play a playlist matching the user's mood. Protects from pause for 5 min."""
        uri = MOOD_PLAYLISTS.get(sentiment)
        if not uri:
            print(f"[Spotify] No playlist mapped for mood: {sentiment}")
            return
        print(f"[Spotify] 🎵 Mood '{sentiment}' → {uri}")
        self._play_playlist(uri)
        self._mood_play_time = time.time()

    def set_volume(self, volume: int):
        """volume: 0-100"""
        try:
            self.sp.volume(volume)
            print(f"[Spotify] 🔊 Ses seviyesi: {volume}%")
        except Exception as e:
            print(f"[Spotify] Ses hatası: {e}")
