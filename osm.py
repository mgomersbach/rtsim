"""
OpenStreetMap Data Cache.
Will stream tiles and combined images from disk.
Will fetch missing tiles if needed.
Will combine tiles into a single image.
Will cache tiles and combined images.
Will ratelimit.
"""

import os
import math
import urllib.request
import logging
import time

import pygame

ZOOMLEVELS = {
    0: { "tiles": 1, "tile_width": 360, "mpixel": 156412, "scale": 1/500000000 }, 
    1: { "tiles": 4, "tile_width": 180, "mpixel": 78206, "scale": 1/250000000 },
    2: { "tiles": 16, "tile_width": 90, "mpixel": 39103, "scale": 1/150000000 },
    3: { "tiles": 64, "tile_width": 45, "mpixel": 19551, "scale": 1/70000000 },
    4: { "tiles": 256, "tile_width": 22.5, "mpixel": 9776, "scale": 1/35000000 },
    5: { "tiles": 1024, "tile_width": 11.25, "mpixel": 4888, "scale": 1/15000000 },
    6: { "tiles": 4096, "tile_width": 5.625, "mpixel": 2444, "scale": 1/10000000 },
    7: { "tiles": 16384, "tile_width": 2.8125, "mpixel": 1222, "scale": 1/4000000 },
    8: { "tiles": 65536, "tile_width": 1.40625, "mpixel": 610.984, "scale": 1/2000000 },
    9: { "tiles": 262144, "tile_width": 0.703125, "mpixel": 305.492, "scale": 1/1000000 },
    10: { "tiles": 1048576, "tile_width": 0.3515625, "mpixel": 152.746, "scale": 1/500000 },
    11: { "tiles": 4194304, "tile_width": 0.17578125, "mpixel": 76.373, "scale": 1/250000 },
    12: { "tiles": 16777216, "tile_width": 0.087890625, "mpixel": 38.187, "scale": 1/125000 },
    13: { "tiles": 67108864, "tile_width": 0.0439453125, "mpixel": 19.093, "scale": 1/62500 },
    14: { "tiles": 268435456, "tile_width": 0.02197265625, "mpixel": 9.547, "scale": 1/32000 },
    15: { "tiles": 1073741824, "tile_width": 0.010986328125, "mpixel": 4.773, "scale": 1/16000 },
    16: { "tiles": 4294967296, "tile_width": 0.0054931640625, "mpixel": 2.387, "scale": 1/8000 },
    17: { "tiles": 17179869184, "tile_width": 0.00274658203125, "mpixel": 1.193, "scale": 1/4000 },
    18: { "tiles": 68719476736, "tile_width": 0.001373291015625, "mpixel": 0.596, "scale": 1/2000 },
    19: { "tiles": 274877906944, "tile_width": 0.0006866455078125, "mpixel": 0.298, "scale": 1/1000 },
    20: { "tiles": 137438953472, "tile_width": 0.00034332275390625, "mpixel": 0.149, "scale": 1/500 },
}

class OSMCache:
    def __init__(self, tile_cache_dir, image_cache_dir, tile_server_url=None):
        self.tile_cache_dir = tile_cache_dir
        self.image_cache_dir = image_cache_dir
        self.tile_server_url = tile_server_url or "https://tile.openstreetmap.org"

        if not os.path.exists(self.tile_cache_dir):
            os.makedirs(self.tile_cache_dir)

        if not os.path.exists(self.image_cache_dir):
            os.makedirs(self.image_cache_dir)

    def _degrees_to_tile(self, lat, lon, zoom):
        lat_rad = math.radians(lat)
        n = 2**zoom
        xtile = int((lon + 180) / 360 * n)
        ytile = int(
            (1 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi)
            / 2
            * n
        )
        return (xtile, ytile)

    def _tile_to_degrees(self, xtile, ytile, zoom):
        n = 2**zoom
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)
        return lat_deg, lon_deg

    def _get_tile_path(self, xtile, ytile, zoom):
        return os.path.join(
            self.tile_cache_dir, str(zoom), str(xtile), str(ytile) + ".png"
        )

    def _get_image_path(self, name, min_lat, max_lat, min_lon, max_lon, zoom):
        topleft = self._degrees_to_tile(max_lat, min_lon, zoom)
        bottomright = self._degrees_to_tile(min_lat, max_lon, zoom)
        topleft_string = f"{topleft[0]}_{topleft[1]}"
        bottomright_string = f"{bottomright[0]}_{bottomright[1]}"
        return os.path.join(
            self.image_cache_dir, name, f"{topleft_string}-{bottomright_string}-{zoom}.png"
        )

    def _get_tile_url(self, xtile, ytile, zoom):
        return f"{self.tile_server_url}/{zoom}/{xtile}/{ytile}.png"

    def _fetch_remote_tile(self, xtile, ytile, zoom):
        url = self._get_tile_url(xtile, ytile, zoom)
        path = self._get_tile_path(xtile, ytile, zoom)
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        print(f"Fetching {url}")
        urllib.request.urlretrieve(url, path)

    def _fetch_tile(self, xtile, ytile, zoom):
        path = self._get_tile_path(xtile, ytile, zoom)
        if not os.path.exists(path):
            print(f"Fetching tile {xtile}, {ytile} remotely")
            self._fetch_remote_tile(xtile, ytile, zoom)
            time.sleep(1)
        return path

    def _write_cached_image(self, image, path):
        if not os.path.exists(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        pygame.image.save(image, path)

    def calculate_bounding_box(self, first_point, second_point):
        min_lat = min(first_point[0], second_point[0])
        max_lat = max(first_point[0], second_point[0])
        min_lon = min(first_point[1], second_point[1])
        max_lon = max(first_point[1], second_point[1])
        return min_lat, max_lat, min_lon, max_lon

    def _create_combined_image(self, min_lat, max_lat, min_lon, max_lon, zoom):
        min_x, min_y = self._degrees_to_tile(max_lat, min_lon, zoom)
        max_x, max_y = self._degrees_to_tile(min_lat, max_lon, zoom)
        new_max_lat, new_min_lon = self._tile_to_degrees(min_x, min_y, zoom)
        new_min_lat, new_max_lon = self._tile_to_degrees(max_x + 1, max_y + 1, zoom)
        pix_width = (max_x - min_x + 1) * 256
        pix_height = (max_y - min_y + 1) * 256
        print(f"Creating combined image of {pix_width}x{pix_height}")
        combined_image = pygame.Surface((pix_width, pix_height))
        combined_image.fill((0, 0, 0))
        print("Fetching", (1 + max_x - min_x) * (1 + max_y - min_y), "tiles")
        for xtile in range(min_x, max_x + 1):
            for ytile in range(min_y, max_y + 1):
                path = self._fetch_tile(xtile, ytile, zoom)
                x_off = 256 * (xtile - min_x)
                y_off = 256 * (ytile - min_y)
                tile = pygame.image.load(path)
                combined_image.blit(tile, (x_off, y_off))
        return combined_image, (new_min_lat, new_max_lat, new_min_lon, new_max_lon)

    def get_combined_image(self, name, first_point, second_point, zoom):
        min_lat, max_lat, min_lon, max_lon = self.calculate_bounding_box(
            first_point, second_point
        )
        #(max_lat, min_lon), (min_lat, max_lon) = topleft, bottomright
        image_path = self._get_image_path(name, min_lat, max_lat, min_lon, max_lon, zoom)
        if not os.path.exists(image_path):
            combined_image = self._create_combined_image(
                min_lat, max_lat, min_lon, max_lon, zoom
            )
            self._write_cached_image(combined_image[0], image_path)
            print("Saved combined image to", image_path)
            return combined_image
        else:
            print("Combined image already exists at", image_path)
            return pygame.image.load(image_path), (min_lat, max_lat, min_lon, max_lon)

opener = urllib.request.build_opener()
opener.addheaders = [("User-agent", "OSMViz/1.1.0 +https://hugovk.github.io/osmviz")]
urllib.request.install_opener(opener)


def _temp_test():
    osm = OSMCache("tilecache\\osm", "imagecache\\osm")
    image = osm.get_combined_image(
        name="home",
        first_point=(52.366544, 4.825636),
        second_point=(52.363799, 4.832556),
        zoom=18,
    )

    pygame.init()
    display_surface = pygame.display.set_mode((640, 480))
    pygame.display.set_caption("Image")
    while True:
        time.sleep(1)
        display_surface.blit(image[0], (0, 0))
        pygame.display.update()

_temp_test()