import requests
import icalendar
import datetime
import os

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
calendar_url = "https://nsps.ca/events/month/?ical=1"
day = datetime.date.today()


def get_events():
    headers = {
        # This is to get around mod_security blocking the request based
        # on the user-agent.
        "User-Agent": "mod_security sucks"
    }
    r = requests.get(calendar_url, headers=headers)
    return r.text


def get_calendar():
    events = get_events()
    return icalendar.Calendar.from_ical(events)


def events_for_day(calendar, day):
    events = []
    for event in calendar.walk("vevent"):
        if event.start.date() == day:
            events.append(event)

    return events


def send_to_slack(events, day):
    client.api_test()
    summary = "📣 {} Scheduled events today *{}*".format(
        len(events), day.strftime("%B %d")
    )
    if len(events) == 1:
        summary = "📣 Scheduled event today *{}*".format(day.strftime("%B %d"))

    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": summary}}]

    for event in events:
        start_time = event.start.strftime("%I:%M %p")
        description = (
            event.description.split("Admission is free for Members")[0]
            .strip()
            .replace("\n", "\n\n")
        )
        blocks.append({"type": "divider"})
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*{}* at *{}*\n{}".format(
                        event.summary, start_time, description
                    ),
                },
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "More info", "emoji": True},
                    "url": event.url,
                    "action_id": "button-action",
                },
            },
        )

    try:
        client.chat_postMessage(channel="#testing-only", text=summary, blocks=blocks)
    except SlackApiError as e:
        print(f"❌ Error sending message to Slack: {e.response['error']}")


if __name__ == "__main__":
    calendar = get_calendar()
    print(f"✅ Found {len(calendar.walk('vevent'))} events in calendar")
    events = events_for_day(calendar, day)
    print(f"✅ Found {len(events)} events for the day {day}")
    send_to_slack(events, day)
    print(f"✅ Sent events to Slack")