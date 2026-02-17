import requests
import os
import datetime
import logging
import websocket
import json
from config import URL, HEADERS
import random

_cached_jwt = None
frames_cache = {}
MAX_CACHE_SIZE = 200
def get_jwt():
    global _cached_jwt
    if _cached_jwt: return _cached_jwt
    user, pw = os.getenv("CHIRPSTACK_USER"), os.getenv("CHIRPSTACK_PASS")
    login_url = f"{URL}/api/internal/login"
    try:
        r = requests.post(login_url, json={"email": user, "password": pw}, timeout=5)
        if r.status_code == 200:
            _cached_jwt = r.json().get("jwt")
            return _cached_jwt
    except Exception as e:
        logging.error(f"Login Error: {e}")
    return None

def get_auth_headers():
    token = get_jwt()
    if not token: return HEADERS
    return {
        "Authorization": f"Bearer {token}",
        "Grpc-Metadata-Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

def format_ts(ts_str):
    """Превращает ISO время в dd.mm.yyyy HH:MM:SS (+5 UTC)"""
    if not ts_str: return "—"
    try:
        clean_ts = ts_str.split('.')[0].replace('Z', '')
        dt = datetime.datetime.fromisoformat(clean_ts)
        dt_plus_5 = dt + datetime.timedelta(hours=5)
        return dt_plus_5.strftime("%d.%m.%Y %H:%M:%S")
    except:
        return ts_str


def save_to_cache(key, data):
    if not data:
        return
    frames_cache[key] = data
    if len(frames_cache) > MAX_CACHE_SIZE:
        oldest_key = next(iter(frames_cache))
        frames_cache.pop(oldest_key)
        logging.info(f"Cache cleanup: removed {oldest_key}")


def fetch_frames(kind, item_id):
    token = get_jwt()
    ws_url = f"{URL.replace('http', 'ws')}/api/{kind}/{item_id}/frames"
    headers = [f"Sec-Websocket-Protocol: Bearer, {token}"]
    captured_frames = []
    try:
        ws = websocket.create_connection(ws_url, header=headers, timeout=2)
        ws.settimeout(0.5)
        try:
            for _ in range(10):
                msg = ws.recv()
                if not msg: break
                captured_frames.append(json.loads(msg))
        except websocket.WebSocketTimeoutException:
            logging.info(f"WS Frames: Captured {len(captured_frames)}")
        ws.close()
    except Exception as e:
        logging.error(f"WS Error: {e}")
    save_to_cache(f"fr_{item_id}", captured_frames)
    return captured_frames


def fetch_events(item_id):
    token = get_jwt()
    ws_url = f"{URL.replace('http', 'ws')}/api/devices/{item_id}/events"
    headers = [f"Sec-Websocket-Protocol: Bearer, {token}"]
    captured_events = []
    try:
        ws = websocket.create_connection(ws_url, header=headers, timeout=2)
        ws.settimeout(0.5)
        try:
            for _ in range(10):
                msg = ws.recv()
                if not msg: break
                captured_events.append(json.loads(msg))
        except websocket.WebSocketTimeoutException:
            logging.info(f"WS Events: Captured {len(captured_events)}")
        ws.close()
    except Exception as e:
        logging.error(f"WS Events Error: {e}")
    save_to_cache(f"ev_{item_id}", captured_events)
    return captured_events

def global_search(query):
    endpoint = f"internal/search?search={query}&limit=10"
    try:
        r = requests.get(f"{URL}/api/{endpoint}", headers=get_auth_headers(), timeout=5)
        return r.json().get('result') or []
    except: return []

def fetch_data(endpoint):
    try:
        r = requests.get(f"{URL}/api/{endpoint}", headers=get_auth_headers(), timeout=5)
        if r.status_code == 200:
            data = r.json()
            return data.get('result', []), int(data.get('totalCount', 0))
        return [], 0
    except: return [], 0

def fetch_item(endpoint):
    try:
        r = requests.get(f"{URL}/api/{endpoint}", headers=get_auth_headers(), timeout=5)
        return r.json() if r.status_code == 200 else None
    except: return None

def fetch_devices(app_id, offset=0, limit=10):
    return fetch_data(f"devices?limit={limit}&offset={offset}&applicationID={app_id}")

def fetch_device_detail(dev_eui):
    return fetch_item(f"devices/{dev_eui}")


def send_device_command(dev_eui, b64_data):
    """Отправляет Base64 команду в очередь устройства ChirpStack"""
    url = f"{URL}/api/devices/{dev_eui}/queue"
    payload = {
        "deviceQueueItem": {
            "devEUI": dev_eui,
            "fPort": random.randint(1, 8),
            "data": b64_data
        }
    }
    try:
        r = requests.post(url, json=payload, headers=get_auth_headers(), timeout=5)
        return r.status_code == 200
    except Exception as e:
        logging.error(f"Send Command Error: {e}")
        return False