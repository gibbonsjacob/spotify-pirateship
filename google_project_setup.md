# Per-User Google API Setup 


If you want each user to have their own YouTube search quota (100/day), each person needs their **own Google Cloud project** and `client_secrets.json`. Follow these steps:

---

### 1. Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Click the button directly to the right of the Google Cloud Logo 
3. Click "New Project".
3. Give it a name (e.g., `Spotify PirateShip - UserName`) and click **Create**.

---

### 2. Enable the YouTube Data API

1. Inside the new project, go to **APIs & Services → Library**(In the Quick Access menu).
2. Click `Enable APIs and Services`
2. Search for **YouTube Data API v3**.
3. Click **Enable**.

---

### 3. Create OAuth Client Credentials

1. In the same screen, click  **Create Credentials**.
2. Configure the Consent Screen 
    - Note that these don't need any real effort, just put your email address and the App Name whenever asked
3. Under `Scopes` I selected all of the scopes under the `Youtube Data API v3` but you only need to use `.../auth/youtube.readonly`
    - This will appear under the ***Sensitive Scopes*** section, hence the need to authenticate
    - This is how we personalize search results
2. Choose **Desktop App** as the application type in the OAuth Client ID Section.
    - Give it a name (e.g., `Spotify Pirate Ship Desktop`).
4. Click **Create**, then **Download**
    >   * Save this as `client_secrets.json`.
    >  * **Do not share this file**; it’s tied to this project and is what affects our rate limits.

---

### 4. Place the file and run the app

1. Move `client_secrets.json` into the same folder as [main.py](./main.py).
2. Run the below script in [get_video_url.py](./get_video_url.py) to authenticate with Google (only done once):

   ```bash
   uv run get_video_url.py --auth
   ```
3. A browser window will open asking you to log in with **your Google account**.
4. After logging in, a `token.pickle` file will be created automatically. This stores your access tokens.

---

### 5. Notes

* Each user must have their own **project and JSON** following the steps above.
* This setup gives each user a **separate 100 searches/day quota**.
* `token.pickle` is created per user and should **not** be shared.
* You can safely commit your Python code to Git, but **never commit `client_secrets.json` or `token.pickle`**.
