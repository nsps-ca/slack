import base64
import os
import sys
import json

from calendar import monthrange
from datetime import datetime, timedelta

import requests
from pyzoom import ZoomClient, err
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

slack_token = os.environ.get("SLACK_BOT_TOKEN", None)
slack_client = WebClient(token=slack_token)
channel = "#it-strategy"

TOKEN_URL = "https://zoom.us/oauth/token"
RECORDINGS_ENDPOINT = "/accounts/me/recordings"
PAGE_SIZE = 100  # Max is 300
DEFAULT_DAYS = 14

ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
assert ZOOM_ACCOUNT_ID
assert ZOOM_CLIENT_ID
assert ZOOM_CLIENT_SECRET


def send_to_slack(recording):
    if not slack_token:
        print("❌ SLACK_BOT_TOKEN environment variable not set, not sending to Slack")
        return 

    slack_client.api_test()
    summary = "📣 A new recording has appeared in Zoom. This notification is sent so you can move it over to the Google Drive and others can see it, if it isn't already there."
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": summary}}]
    blocks.append(
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "",
            },
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "{}".format(recording["topic"]),
            },
            "accessory": {
                "type": "button",
                "text": {"type": "plain_text", "text": "Play", "emoji": True},
                "url": "{}?pwd={}".format(recording["share_url"], recording["recording_play_passcode"]),
                "action_id": "button-action",
            },
        },
    )

    try:
        slack_client.chat_postMessage(channel=channel, text=summary, blocks=blocks)
    except SlackApiError as e:
        print(f"❌ Error sending message to Slack: {e.response['error']}")


def access_token(account_id: str, client_id: str, client_secret: str) -> str:
    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    response = requests.post(
        TOKEN_URL,
        params={"grant_type": "account_credentials", "account_id": account_id},
        headers={"Authorization": f"Basic {credentials}"},
        timeout=30,
    )
    if response.status_code != 200:
        reason = response.json().get("reason", response.text) if response.text else ""
        raise RuntimeError(
            f"Zoom refused the credentials ({response.status_code}): {reason}"
        )
    return response.json()["access_token"]


def recordings(client: ZoomClient, start: date, end: date) -> list[dict]:
    query = {
        "page_size": PAGE_SIZE,
        "from": start.isoformat(),
        "to": end.isoformat(),
    }
    page = client.raw.get(RECORDINGS_ENDPOINT, query=query).json()
    return page.get("meetings") or []


def account_recordings(client: ZoomClient, start: date, end: date) -> list[dict]:
    meetings = recordings(client, start, end)
    meetings.sort(key=lambda meeting: meeting.get("start_time") or "")
    return meetings


if __name__ == "__main__":
    end = datetime.today()
    start = end - timedelta(days=DEFAULT_DAYS)

    token = access_token(
        ZOOM_ACCOUNT_ID,
        ZOOM_CLIENT_ID,
        ZOOM_CLIENT_SECRET,
    )
    client = ZoomClient(token)
    try:
        recordings = account_recordings(client, start, end)
    except err.APIError as e:
        print(f"❌ Zoom API error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"✅ Got list of recordings from Zoom")

    with open(".seen-recordings", "r") as f:
        seen_recordings = json.load(f)

    for recording in recordings:
        if recording["uuid"] not in seen_recordings:
            print(f"📣 Sending notification about {recording['uuid']}.")
            send_to_slack(recording)
            seen_recordings.insert(0, recording["uuid"])
        else:
            print(f"✅ Ignoring uuid {recording['uuid']} we've seen it before.")
    
    with open(".seen-recordings", "w") as f:
        json.dump(seen_recordings, f, indent=2)