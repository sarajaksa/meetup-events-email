import datetime
import json
import re
import smtplib
import ssl
import sys

import requests

from config import city, lat, lon
from email_config import email, email_password, email_port, email_server

start_of_week = datetime.timedelta(days=7 - datetime.datetime.now().weekday())
duration_of_week = datetime.timedelta(days=7)
start_date = (datetime.datetime.now() + start_of_week).isoformat().split("T")[
    0
] + "T00:00:00"
end_date = (
    datetime.datetime.now() + start_of_week + duration_of_week
).isoformat().split("T")[0] + "T00:00:00"

url_events = "https://api.meetup.com/gql"
url_main_site = "https://meetup.com"
subject = "Subject: The meetup events next week\n\n"
post_data = {
    "operationName": "categoryEvents",
    "variables": {
        "endDateRange": end_date,
        "startDateRange": start_date,
        "lat": lat,
        "lon": lon,
        "first": 1000,
    },
    "query": "query categoryEvents($lat: Float!, $lon: Float!, $topicId: Int, $startDateRange: DateTime, $endDateRange: DateTime, $first: Int, $after: String) {searchEvents: upcomingEvents(search: {lat: $lat, lon: $lon, categoryId: $topicId, startDateRange: $startDateRange, endDateRange: $endDateRange}, input: {first: $first, after: $after}) {edges {node {group {name} link title dateTime venue {city venueType}}}}}",
}


def get_message_for_event(event):
    return f'{event["title"]} ({event["group"]["name"]})\n{event["dateTime"]}\n{event["link"]}'


meetup_response = requests.get(url_main_site)
if not meetup_response.ok:
    sys.exit()

meetup_response.headers["Set-cookie"]
cookies = re.match(
    r"MEETUP_BROWSER_ID=\"([\S\s]+?)\"", meetup_response.headers["Set-cookie"]
).group()

response = requests.post(url_events, json=post_data, headers={"Cookie": cookies})
if not response.ok:
    sys.exit()

data = json.loads(response.text)
events = data["data"]["searchEvents"]["edges"]
events_in_person = [
    get_message_for_event(event["node"])
    for event in events
    if event["node"]["venue"]["venueType"] != "online"
    and event["node"]["venue"]["city"] == city
]
message = "\n\n\n------------------------------------\n\n\n".join(events_in_person)
message = (
    message.replace("Å¡", "s")
    .replace("Å\xa0", "S")
    .replace("Ä�", "c")
    .replace("Å¾", "z")
    .replace("ÄŒ", "C")
)

with smtplib.SMTP_SSL(
    email_server, email_port, context=ssl.create_default_context()
) as server:
    server.login(email, email_password)
    server.sendmail(email, email, subject + message)
