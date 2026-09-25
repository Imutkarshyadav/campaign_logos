import pandas as pd
import requests
import os
import re
import urllib.parse

TABS = {
    "AD CAMPAIGNS": "1657559578",
    "XC": "887911653",
    "GZ": "1770634798",
    "ES CAMPAIGNS": "373008080",
    "MI CAMPAIGNS": "913012655"
}

BASE_URL = "https://docs.google.com/spreadsheets/d/1EHEz3cbsFb6xsFrxcZBe7RVx9AOsfy74i_SIdrgGqEk/export?format=csv&gid="

# Since this will run inside the GitHub repo, we save directly to the root or campaign_logos folder.
# Based on how they uploaded it, the files might be in the root or in a campaign_logos folder.
# Let's save them directly to the root to make URLs cleaner, OR match what they have. 
# We'll save to 'campaign_logos' folder if they want to keep it organized.
SAVE_DIR = "campaign_logos"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

def clean_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", str(name)).strip()

def sync_logos():
    dfs = []
    for tab, gid in TABS.items():
        try:
            print(f"Fetching {tab}...")
            df = pd.read_csv(f"{BASE_URL}{gid}")
            if 'Name' in df.columns and 'Logo Link' in df.columns:
                dfs.append(df)
        except Exception as e:
            print(f"Error reading {tab}: {e}")

    if not dfs:
        return

    df = pd.concat(dfs, ignore_index=True)
    df = df.dropna(subset=['Name', 'Logo Link'])
    df = df.drop_duplicates(subset=['Name'])

    for _, row in df.iterrows():
        name = clean_filename(row['Name'])
        url = row['Logo Link']
        
        # We need to save the file exactly as we expect it in the Streamlit app
        file_name = f"{name}.png"
        file_path = os.path.join(SAVE_DIR, file_name)
        
        if os.path.exists(file_path):
            continue # Already backed up!
            
        print(f"Found new logo: {name} -> Downloading...")
        try:
            r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            if r.status_code == 200 and 'image' in r.headers.get('Content-Type', '').lower():
                with open(file_path, 'wb') as f:
                    f.write(r.content)
                print(f"SUCCESS: {name}.png saved.")
            else:
                print(f"FAIL: Invalid image URL for {name}.")
        except Exception as e:
            print(f"FAIL: Network error for {name}. {e}")

if __name__ == "__main__":
    sync_logos()
