import os
import pickle
import google
import json
import argparse
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors


client_secrets_file = "client_secret.json"
scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


def search(search_query: str) -> list:
    
    creds = None

    # Token file stores the user's access and refresh tokens
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)

    # If no valid credentials, or expired, go through flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(google.auth.transport.requests.Request())
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, scopes
            )
            creds = flow.run_local_server(port=0)

        # Save the credentials for next time
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)

    try:
        request = youtube.search().list(
            part="snippet",
            q=search_query,
            maxResults=1,
        )
        response = request.execute()

        for item in response.get("items", []):
            if item["id"]["kind"] == "youtube#video":
                title = item["snippet"]["title"]
                video_id = item["id"]["videoId"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                return {'status': 1,  ## I couldn't remember the actual status code off the top of my head so we're using 1 instead
                        'youtube_url': video_url}

    except googleapiclient.errors.HttpError as e:
        payload_str = e.content.decode('utf-8')
        data = json.loads(payload_str)
        error_code = data['error']['code']
        error_message = data['error']['message']
        errors_list = data['error']['errors']
        context = errors_list[0].get('reason') if errors_list else None
        return {
                'status': e.resp.status, 
                'error_code': error_code,
                'error_message': error_message, 
                'errors_list': errors_list,
                'context': context
                }

def main(args):

    if args.auth:
        # Go through flow
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, scopes
        )
        creds = flow.run_local_server(port=0)

        # Save the credentials for next time
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)  


    search()       


if __name__ == '__main__': 

    parser = argparse.ArgumentParser(description='Authenticate project with Google')
    parser.add_argument('--auth',   action="store_true", help="Establish authentication with Google Project")

    args = parser.parse_args()

    main(args)