import pandas as pd
import datetime
import math
import os
from io import StringIO
import base64, hashlib
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet
from voice_memo import get_master_password

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))

def load_encrypted_points():
    """Loads and decrypts points from points.csv.enc using the master password."""
    try:
        master_password = get_master_password()
    except Exception as e:
        print("Error retrieving master password:", e)
        return pd.DataFrame()
    
    try:
        with open("points.csv.enc", "rb") as f:
            encrypted_data = f.read()
        salt_points = b'points_salt'
        key = derive_key(master_password, salt_points)
        fernet = Fernet(key)
        decrypted_data = fernet.decrypt(encrypted_data)
        decrypted_str = decrypted_data.decode("utf-8")
        df = pd.read_csv(StringIO(decrypted_str))
    except Exception as e:
        print("Error decrypting points file:", e)
        return pd.DataFrame()
    
    # Normalize and adjust column names.
    df.columns = df.columns.str.strip().str.lower()
    if "lat" in df.columns and "latitude" not in df.columns:
        df = df.rename(columns={"lat": "latitude"})
    if "lon" in df.columns and "longitude" not in df.columns:
        df = df.rename(columns={"lon": "longitude"})
    df["available_from"] = pd.to_datetime(df["available_from"])
    df["available_to"] = pd.to_datetime(df["available_to"])
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df["radius"] = pd.to_numeric(df["radius"], errors="coerce")
    return df

def load_points():
    """
    Loads points from the encrypted points.csv.enc if available,
    otherwise from the plain points.csv.
    Expected columns: latitude, longitude, radius, available_from, available_to, pointer_text, voice_memo (optional)
    """
    if os.path.exists("points.csv.enc"):
        df = load_encrypted_points()
    else:
        try:
            df = pd.read_csv("points.csv")
            df.columns = df.columns.str.strip().str.lower()
            if "lat" in df.columns and "latitude" not in df.columns:
                df = df.rename(columns={"lat": "latitude"})
            if "lon" in df.columns and "longitude" not in df.columns:
                df = df.rename(columns={"lon": "longitude"})
            df["available_from"] = pd.to_datetime(df["available_from"])
            df["available_to"] = pd.to_datetime(df["available_to"])
            df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
            df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
            df["radius"] = pd.to_numeric(df["radius"], errors="coerce")
        except Exception as e:
            print("Error loading points:", e)
            return pd.DataFrame()
    return df

def haversine(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on Earth (in kilometers)."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def get_closest_locations(user_lat, user_lon, df, n=10):
    """
    Returns a DataFrame with the n closest locations to the user.
    Includes: pointer_text, radius, active_period, voice_memo (if present)
    """
    if df.empty:
        return df
    df = df.copy()
    df["distance"] = df.apply(lambda row: haversine(user_lat, user_lon, row["latitude"], row["longitude"]), axis=1)
    df["active_period"] = df.apply(lambda row: f"{row['available_from'].date()} to {row['available_to'].date()}", axis=1)
    closest = df.nsmallest(n, "distance")
    cols = ["pointer_text", "radius", "active_period"]
    if "voice_memo" in closest.columns:
        cols.append("voice_memo")
    return closest[cols]
