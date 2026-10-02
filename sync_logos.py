import pandas as pd
import requests
import os
import re
import urllib.parse

SHEET_ID = "1EHEz3cbsFb6xsFrxcZBe7RVx9AOsfy74i_SIdrgGqEk"
HTML_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/htmlview"
BASE_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid="

def get_dynamic_sheets():
    try:
        r = requests.get(HTML_URL, timeout=10)
        matches = re.findall(r'\{name:\s*\"(.*?)\",.*?gid:\s*\"(.*?)\"', r.text)
        return {name: gid for name, gid in matches}
    except Exception as e:
        print("Failed to load dynamic tabs:", e)
        return {}

TABS = get_dynamic_sheets()

# Since this will run inside the GitHub repo, we save directly to the root or campaign_logos folder.
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
        
        file_name = f"{name}.png"
        file_path = os.path.join(SAVE_DIR, file_name)
        
        # Overwrite existing logos if they already exist, so updates work correctly.
        # if os.path.exists(file_path):
        #     continue 
            
        print(f"Found brand new campaign: {name} -> Downloading...")
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
