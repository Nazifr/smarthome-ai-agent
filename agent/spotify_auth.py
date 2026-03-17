"""
Spotify Auth Scripti

Bu scripti bir kez çalıştırarak Spotify hesabına erişim izni al.
Token otomatik olarak cache'lenecek ve sistem her başladığında kullanılacak.

Çalıştırma:
    python spotify_auth.py
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

CLIENT_ID     = os.getenv("SPOTIFY_CLIENT_ID", "")     or input("Spotify Client ID: ").strip()
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "") or input("Spotify Client Secret: ").strip()
REDIRECT_URI  = "http://127.0.0.1:8888/callback"

# Gerekli izinler
SCOPE = "user-modify-playback-state user-read-playback-state playlist-read-private"

print("\nSpotify hesabına bağlanılıyor...")
print("Tarayıcıda izin sayfası açılacak, izin ver ve yönlendirilen URL'yi kopyala.\n")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=".spotify_cache"
))

# Bağlantıyı test et
user = sp.current_user()
print(f"✅ Bağlandı! Kullanıcı: {user['display_name']}")

# Mevcut playlist'leri listele
print("\n📋 Playlist'lerin:")
playlists = sp.current_user_playlists(limit=10)
for i, pl in enumerate(playlists["items"]):
    print(f"  {i+1}. {pl['name']} — {pl['uri']}")

print("\n✅ Token kaydedildi: .spotify_cache")
print("Bu URI'leri label_mapping.json'a ekleyebilirsin.")
