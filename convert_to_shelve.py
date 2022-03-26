#!/usr/bin/env python
"""Holds various functions for converting, sanitizing, and storing data."""

import shelve
import json
import unicodedata

from Airports import Airport

def convert_airports_json():
    """Convert the airports in the json to entries in the airports shelve."""
    with open("datasources/airport-codes_json.json") as f:
        airports = json.load(f)
    print("Amount of airports", len(airports), "in json")
    with shelve.open("db/airports") as db:
        for airport in airports:
            db[airport["ident"]] = Airport(
                airport["ident"],
                airport["type"],
                airport["name"].encode("utf-8"),
                airport["elevation_ft"],
                airport["continent"],
                airport["iso_country"],
                airport["iso_region"],
                airport["municipality"],
                airport["gps_code"],
                airport["iata_code"],
                airport["local_code"],
                airport["coordinates"],
            )
        print("Amount of airports", len(db.keys()), "in shelve")


convert_airports_json()

communications = ""