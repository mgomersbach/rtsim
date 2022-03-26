import pygame
import Runways

class Airport:
    """Create an Airport object that holds ident, type, name, elevation_ft, continent,
    iso_country, iso_region, municipality, gps_code, iata_code, local_code and coordinates."""

    def __init__(
        self,
        ident,
        type,
        name,
        elevation_ft,
        continent,
        iso_country,
        iso_region,
        municipality,
        gps_code,
        iata_code,
        local_code,
        coordinates,
        runways,
        screen,
    ):
        """Initialize an Airport object."""
        self.ident = ident
        self.type = type
        self.name = name
        self.elevation_ft = elevation_ft
        self.continent = continent
        self.iso_country = iso_country
        self.iso_region = iso_region
        self.municipality = municipality
        self.gps_code = gps_code
        self.iata_code = iata_code
        self.local_code = local_code
        self.coordinates = coordinates
        self.runways = runways
        self.screen = screen

    def draw_runways(self):
        """Draw the runways of an airport."""
        for runway in self.runways:
            runway.draw(self.screen)
