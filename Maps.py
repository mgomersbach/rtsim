import math
from typing import Dict, List, Tuple


class Map:
    """Tile System math for the Spherical Mercator projection coordinate system (EPSG:3857)"""

    def __init__(self):
        self.radius = float(6378137)
        self.max_latitude = float(85.05112878)
        self.min_latitude = float(-85.05112878)
        self.max_longitude = float(180)
        self.min_longitude = float(-180)

    def clip(self, to_clip: float, min_clip: float, max_clip: float) -> float:
        """Clip a number to a range.

        Args:
            to_clip (float): The number to clip.
            min_clip (float): The minimum value to clip to.
            max_clip (float): The maximum value to clip to.

        Returns:
            float: The clipped number.
        """
        return min(max(to_clip, min_clip), max_clip)

    def map_size(self, zoom: float, tile_size: int) -> float:
        """Return the size of the map in pixels at a certain zoom level.

        Args:
            zoom (float): Zoom Level to calculate width at.
            tile_size (int): The size of the tiles in the tile pyramid.

        Returns:
            float: Width and height of the map in pixels.
        """

        return math.ceiling(tile_size * math.pow(2, zoom))

    def ground_resolution(self, lat: float, zoom: float, tile_size: int) -> float:
        """Return the ground resolution (meters per pixel) for a given latitude, zoom level, and tile size.

        Args:
            lat (float): Degree of latitude to calculate resolution at.
            zoom (float): Zoom level to calculate resolution at.
            tile_size (int): The size of the tiles in the tile pyramid.

        Returns:
            float: Ground resolution in meters per pixels.
        """
        return (
            math.cos(lat * math.pi / 180)
            * 2
            * math.pi
            * self.radius
            / self.map_size(zoom, tile_size)
        )

    def map_scale(self, lat: float, zoom: float, tile_size: int, dpi: int) -> float:
        """Return the map scale at a certain zoom level.

        Args:
            lat (float): Latitude (in degrees) at which to measure the map scale.
            zoom (float): Level of detail, from 1 (lowest detail) to 23 (highest detail).
            tile_size (int): The size of the tiles in the tile pyramid.
            dpi (int): Resolution of the screen, in dots per inch.

        Returns:
            float: The map scale, expressed as the denominator N of the ratio 1 : N.
        """
        return self.ground_resolution(lat, zoom, tile_size) * dpi / 0.0254

    def pixel_to_position(self, pixel: float, zoom: float, tile_size: int) -> float:
        """Global Converts a Pixel coordinate into a geospatial coordinate at a specified zoom level.
        Global Pixel coordinates are relative to the top left corner of the map (90, -180)

        Args:
            pixel (float): Pixel coordinates in the format of (x, y).
            zoom (float): Zoom level.
            tile_size (int): The size of the tiles in the tile pyramid.

        Returns:
            float: A position value in the format (longitude, latitude).
        """
        mapsize = self.map_size(zoom, tile_size)
        x = (self.clip(pixel[0], 0, mapsize - 1) / mapsize) - 0.5
        y = 0.5 - (self.clip(pixel[1], 0, mapsize - 1) / mapsize)
        return 360 * x, 90 - 360 * math.atan(math.exp(-y * 2 * math.pi)) / math.pi

    def position_to_pixel(self, position: float, zoom: int, tile_size: int) -> float:
        """Converts a point from latitude/longitude WGS-84 coordinates (in degrees) into pixel XY coordinates at a specified level of detail.

        Args:
            position (float): Position coordinate in the format (longitude, latitude)
            zoom (int): Zoom level.
            tile_size (int): The size of the tiles in the tile pyramid.

        Returns:
            float: A global pixel coordinate.
        """
        latitude = self.clip(position[1], self.min_latitude, self.max_latitude)
        longitude = self.clip(position[0], self.min_longitude, self.max_longitude)
        x = (longitude + 180) / 360
        sin_latitude = math.sin(latitude * math.pi / 180)
        y = 0.5 - (math.log((1 + sin_latitude) / (1 - sin_latitude)) / (4 * math.pi))
        mapsize = self.map_size(zoom, tile_size)
        return self.clip(x * mapsize + 0.5, 0, mapsize - 1), self.clip(
            y * mapsize + 0.5, 0, mapsize - 1
        )

    def pixel_to_tilexy(self, pixel: float, tile_size: int) -> float:
        """Converts pixel XY coordinates into tile XY coordinates of the tile containing the specified pixel.

        Args:
            pixel (float): Pixel coordinates in the format of (x, y).
            tile_size (int): The size of the tiles in the tile pyramid.

        Returns:
            float: Tile coordinates in the format of (x, y).
        """
        return int(pixel[0] / tile_size), int(pixel[1] / tile_size)

    def scale_pixel(self, pixel: float, old_zoom: float, new_zoom: float) -> float:
        """Performs a scale transform on a global pixel value from one zoom level to another.

        Args:
            pixel (float): Pixel coordinates in the format of (x, y).
            old_zoom (float): The zoom level in which the input global pixel value is from.
            new_zoom (float): The zoom level in which the output global pixel value is to.

        Returns:
            float: The scaled global pixel value.
        """
        scale = math.power(2, new_zoom - old_zoom)
        return pixel[0] * scale, pixel[1] * scale

    def scale_pixels(
        self, pixels: List[Dict[float, float]], old_zoom: float, new_zoom: float
    ) -> List[Dict[float, float]]:
        """Performs a scale transform on a list of global pixel values from one zoom level to another.

        Args:
            pixels (List[Dict[float, float]]): A list of global pixel value from the old zoom level. Points are in the format of (x, y).
            old_zoom (float): The zoom level in which the input global pixel values is from.
            new_zoom (float): The new zoom level in which the output global pixel values should be aligned with.

        Returns:
            float: A list of global pixel values that has been scaled for the new zoom level.
        """
        scale = math.power(2, new_zoom - old_zoom)
        output = []
        for pixel in pixels:
            output.append(pixel[0] * scale, pixel[1] * scale)
        return output

    def tilexy_to_pixel(self, tilex: int, tiley: int, tilesize: int) -> float:
        """Converts tile XY coordinates into pixel XY coordinates of the upper-left pixel of the specified tile.

        Args:
            tilex (int): Tile X coordinate.
            tiley (int): Tile Y coordinate.
            tilesize (int): The size of the tiles in the tile pyramid.

        Returns:
            float: Pixel coordinates in the format of (x, y).
        """
        return tilex * tilesize, tiley * tilesize

    def tilexy_to_quadkey(self, tilex: int, tiley: int, zoom: int) -> str:
        """Converts tile XY coordinates into a quadkey at a specified level of detail.

        Args:
            tilex (int): Tile X coordinate.
            tiley (int): Tile Y coordinate.
            zoom (int): Level of detail, from 1 (lowest detail) to 23 (highest detail).

        Returns:
            str: A quadkey.
        """
        quadkey = ""
        for i in range(zoom, 0, -1):
            digit = 0
            mask = 1 << (i - 1)
            if tilex & mask != 0:
                digit += 1
            if tiley & mask != 0:
                digit += 2
            quadkey += str(digit)
        return quadkey

    def quadkey_to_tilexy(self, quadkey: str) -> Tuple[int, int, int]:
        """Converts a quadkey into tile XY coordinates.

        Args:
            quadkey (str): The quadkey.

        Returns:
            Tuple(int, int, int): Tile X, Y coordinates and zoom level.
        """
        tilex = 0
        tiley = 0
        zoom = len(quadkey)
        for i in range(zoom, 0, -1):
            mask = 1 << (i - 1)
            if quadkey[zoom - i] == "0":
                pass
            elif quadkey[zoom - i] == "1":
                tilex += mask
            elif quadkey[zoom - i] == "2":
                tiley += mask
            elif quadkey[zoom - i] == "3":
                tilex += mask
                tiley += mask
        return tilex, tiley, zoom

    def position_to_tilexy(
        self, position: float, zoom: int, tile_size: int
    ) -> Tuple[float, float]:
        """Calculates the XY tile coordinates that a coordinate falls into for a specific zoom level.

        Args:
            position (float): Position coordinate in the format (longitude, latitude)
            zoom (int): Zoom level.
            tile_size (int): The size of the tiles in the tile pyramid.

        Returns:
            Tuple(float, float): Tile X, Y coordinates and zoom level.
        """
        latitude = self.clip(position[1], self.min_latitude, self.max_latitude)
        longitude = self.clip(position[0], self.min_longitude, self.max_longitude)
        x = (longitude + 180) / 360
        sin_latitude = math.sin(latitude * math.pi / 180)
        y = 0.5 - (math.log((1 + sin_latitude) / (1 - sin_latitude)) / (4 * math.pi))
        mapsize = self.map_size(zoom, tile_size)
        tilex = int(
            math.floor(self.clip(x * mapsize + 0.5, 0, mapsize - 1) / tile_size)
        )
        tiley = int(
            math.floor(self.clip(y * mapsize + 0.5, 0, mapsize - 1) / tile_size)
        )
        return tilex, tiley

    def quadkey_from_view(
        self, position: float, zoom: int, width: int, height: int, tile_size: int
    ) -> List[str]:
        """ Calculates the tile quadkey strings that are within a specified viewport.

        Args:
            position (float): Position coordinate in the format (longitude, latitude)
            zoom (int): Zoom level.
            width (int): Width of the viewport in pixels.
            height (int): Height of the viewport in pixels.
            tile_size (int): The size of the tiles in the tile pyramid.

        Returns:
            List(str): A list of tile quadkeys.
        """
        p = self.position_to_tilexy(position, zoom, tile_size)
        top = p[1] - int(height / tile_size / 2)
        left = p[0] - int(width / tile_size / 2)
        bottom = p[1] + int(height / tile_size / 2)
        right = p[0] + int(width / tile_size / 2)
        topleft = self.pixel_to_position((left, top), zoom, tile_size)
        bottomright = self.pixel_to_position((right, bottom), zoom, tile_size)
        bounds = [topleft[0], bottomright[1], bottomright[0], topleft[1]]
        return self.quadkey_from_bounds(bounds, zoom, tile_size)

    def quadkey_from_bounds(self, bounds: float, zoom: int, tile_size: int) -> List[str]:
        """Calculates the tile quadkey strings that are within a bounding box at a specific zoom level.
        Args:
            bounds (float): A bounding box defined as an array of numbers in the format of [west, south, east, north].
            zoom (int): Zoom level.
            tile_size (int): The size of the tiles in the tile pyramid.

        Returns:
            List(str): A list of tile quadkeys.
        """        
        keys = []
        if len(bounds) >= 4:
            topleft, bottomright = self.position_to_tilexy(
                (bounds[3], bounds[0]), zoom, tile_size
            ), self.position_to_tilexy((bounds[1], bounds[2]), zoom, tile_size)
            i = iter(range(topleft[0], bottomright[0] + 1))
            j = iter(range(topleft[1], bottomright[1] + 1))
            for x in i:
                for y in j:
                    keys.append(self.tilexy_to_quadkey(x, y, zoom))
        return keys

    def tilexy_to_boundingbox(self, tilex: int, tiley: int, zoom: float, tile_size: int) -> List[Tuple[float, float, float, float]]:
        """Calculates the bounding box of a tile.

        Args:
            tilex (int): Tile X coordinate.
            tiley (int): Tile Y coordinate.
            zoom (int): Zoom level.
            tile_size (int): The size of the tiles in the tile pyramid.

        Returns:
            List(float, float, float, float): A bounding box defined as an array of numbers in the format of [west, south, east, north].
        """        
        x1 = float(tilex * tile_size)
        y1 = float(tiley * tile_size)
        x2 = float(x1 + tile_size)
        y2 = float(y1 + tile_size)
        nw = self.pixel_to_position((x1, y1), zoom, tile_size)
        se = self.pixel_to_position((x2, y2), zoom, tile_size)
        return [nw[0], se[1], se[0], nw[1]]

    def best_map_view(self, bounds: List[Tuple[float, float, float, float]], map_width: float, map_height: float, padding: int, tile_size: int) -> Tuple[float, float, float]:
        """Calculates the best map view (center, zoom) for a bounding box on a map.

        Args:
            bounds (List(float, float, float, float)): A bounding box defined as an array of numbers in the format of [west, south, east, north].
            map_width (float): Width of the map in pixels.
            map_height (float): Height of the map in pixels.
            padding (int): The padding in pixels to add to the bounding box.
            tile_size (int): The size of the tiles in the tile pyramid. 

        Returns:
            Tuple(float, float, float): A dictionary containing the center, coordinates and zoom of the best view.
        """        
        if len(bounds) < 4:
            center_lat, center_lon, zoom = float(0), float(0), int(1)
            return center_lat, center_lon, zoom

        bounds_deltax = float
        if bounds[2] > bounds[0]:
            bounds_deltax = bounds[2] - bounds[0]
            center_lon = float((bounds[2] + bounds[0]) / 2)
        else:
            bounds_deltax = 360 - (bounds[0] - bounds[2])
            center_lon = float(((bounds[2] + bounds[0]) / 2 + 360) % 360 - 180)

        ry1 = math.log(math.sin(bounds[1] * math.pi / 180) + 1) / math.cos(
            bounds[1] * math.pi / 180
        )
        ry2 = math.log(math.sin(bounds[3] * math.pi / 180) + 1) / math.cos(
            bounds[3] * math.pi / 180
        )
        ryc = (ry1 + ry2) / 2

        center_lat = math.atan(math.sin(ryc)) * 180 / math.pi

        h_reso = bounds_deltax / (map_width - padding * 2)

        vy0 = math.log(math.tan(math.pi * (0.25 + center_lat / 360)))
        vy1 = math.log(math.tan(math.pi * (0.25 + bounds[3] / 360)))
        zoom_factor = (map_height * 0.5 - padding) / (40.74366543152561 * (vy1 - vy0))
        v_reso = 360.0 / (zoom_factor * tile_size)
        reso = max(h_reso, v_reso)
        zoom = math.log(360 / (reso * tile_size), 2)
        return center_lat, center_lon, zoom
