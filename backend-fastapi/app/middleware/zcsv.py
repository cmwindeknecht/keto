import csv
import datetime
from typing import Optional

import httpx
import pytz
from fastapi import requests


class Event:
    def __init__(self, event_id: str, event_title: str, tickets_sold: int):
        self.event_id: str = event_id
        self.event_title: str = event_title
        self.tickets_sold: int = tickets_sold

    def add_market_share(self, capacity: float) -> float:
        self.market_share = self.tickets_sold / capacity
        return self.market_share


class Venue:
    def __init__(self, venue_id: int, capacity: int):
        self.venue_id: int = venue_id
        self.capacity: int = capacity
        self.average_market_share: float = 0.0
        self.events: dict[int, Event] = {}

    def add_event(self, event: Event) -> None:
        if self.events.get(event.event_id, None) is not None:
            print(f"Event {event.event_id} already exists for venue {self.venue_id}")
            return
        self.events[event.event_id] = event
        # TODO study this calculation
        event_market_share = event.add_market_share(self.capacity)
        # TODO fucked it up even when I looked at it --- should += NOT just =
        self.average_market_share = (event_market_share - self.average_market_share) / len(self.events)


class TicketShare:
    EVENT_ID = "event_id"
    VENUE_ID = "venue_id"
    EVENT_TITLE = "event_title"
    DATE = "date"
    TICKETS_SOLD = "tickets_sold"

    # Problem 1 - Event with Highest Market Share
    # Problem 2 - Venue with Highest Average Market Share

    def __init__(self, year: int = 2017, newline_delimeter: str = "\n"):
        self.year = year
        self.newline_delimeter = newline_delimeter
        self.venues: dict[int, Venue] = {}
        self.failed_event_ids: list[int] = []

    def update_newline_delimeter(self, newline_delimeter: str) -> None:
        self.newline_delimeter = newline_delimeter

    async def read_csv(self, filepath: str) -> None:
        with open(filepath, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                event_id = row.get(self.EVENT_ID, None)
                if event_id is None:
                    print(f"Invalid event_id {event_id}")
                    continue

                date = row.get(self.DATE, None)  # Need to know how the date is formatted, if its a timestamp, etc
                # TODO study how to convert dates
                date_from_timestamp = datetime.fromtimestamp(date)
                date_from_string = datetime.strptime(date, "%Y-%m-%d")
                date_with_tz_from_string = datetime.strptime(date, "%Y-%m-%d %H:%M:%S%z")
                date_with_tz_from_string_eastern = date_with_tz_from_string.astimezone(pytz.timezone("US/Eastern"))

                if not self._validate_date(date_with_tz_from_string_eastern):
                    print(f"Invalid date {date_with_tz_from_string} for event {event_id}")
                    continue

                # strings, ints?
                venue_id = row.get(self.VENUE_ID, None)
                event_title = row.get(self.EVENT_TITLE, None)
                tickets_sold = row.get(self.TICKETS_SOLD, None)

                if venue_id is None or event_title is None or tickets_sold is None:
                    print(f"Invalid event data: venue id {venue_id} event_title {event_title} tickets_sold {tickets_sold}")
                    continue

                try:
                    venue_id = int(venue_id)
                    tickets_sold = int(tickets_sold)
                except ValueError as e:
                    print(f"Invalid data due to ValueError {e}")
                    continue

                venue: Optional[Venue] = await self._get_venue(venue_id)
                if venue is None:
                    print(f"Unable to create venue for {venue_id}")
                    continue

                event: Event = Event(event_id=event_id, event_title=event_title, tickets_sold=tickets_sold)
                venue.add_event(event=event)

    def get_event_with_highest_market_share(self):
        top_market_share: Optional[Event] = None
        for venue in self.venues.values():
            for event in venue.events.values():
                if top_market_share is None or top_market_share.market_share < event.market_share:
                    top_market_share = event
        print(f"Top event is {top_market_share.event_title}({top_market_share.event_id}) with {round(top_market_share.market_share, 2)}%")

    def get_venue_with_highest_average_market_share(self):
        top_market_share: Optional[Venue] = None
        for venue in self.venues.values():
            if top_market_share is None or top_market_share.average_market_share < venue.average_market_share:
                top_market_share = venue
        print(f"Top Market Share Average Venue is {top_market_share.venue_id} with {round(top_market_share.average_market_share, 2)}%")

    def _validate_date(self, date: datetime) -> bool:
        return date is not None and date.year == self.year

    async def _get_venue(self, venue_id) -> Optional[Venue]:
        venue: Optional[Venue] = self.venues.get(venue_id, None)
        if venue is None:
            try:
                capacity = await self._get_capacity_data(venue_id)
                venue = Venue(venue_id=venue_id, capacity=capacity)
                self.venues[venue_id] = venue
                return venue
            except httpx.HTTPStatusError as e:
                print(f"Failed to retrieve capacity for venue {venue_id}")
        return venue

    # TODO study making requests
    async def _get_capacity_data(self, venue_id: int) -> int:
        # GET
        response = requests.get("https://api.example.com/items/1")
        response.raise_for_status()  # throws if 4xx/5xx
        data = response.json()

        # GET async
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.example.com/items/1")
            response.raise_for_status()
            return response.json()

        # POST
        response = requests.post("https://api.example.com/items", json={"name": "thing", "price": 9.99})
        response.raise_for_status()  # throws if 4xx/5xx
        data = response.json()

        # POST async
        async with httpx.AsyncClient() as client:
            response = await client.post("https://api.example.com/items", json={"name": "thing", "price": 9.99})
            response.raise_for_status()
            return response.json()

        return 1
