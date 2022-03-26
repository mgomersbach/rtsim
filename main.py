#!/usr/bin/env python3

"""Create a simulator of airplane flights between airports and visualize these on a map.
Use pygame to draw the screen with the map, airports, runways, take user inputs and update airplane positions.
Automatically convert between screen map and real life coordinates.
"""

import os
import random
import time

import pygame
from pygame.locals import *

import Airports
import Maps
import osm


class Airplane:
    """An airplane with a length, width, position, speed, and direction."""

    def __init__(self, length, width, lat, lon, speed, direction):
        self.length = length
        self.width = width
        self.lat = lat
        self.lon = lon
        self.speed = speed
        self.direction = direction

class App:
    def __init__(self):
        self.running = True
        self.size = (800, 600)
        self.zoom_image = 1
        self.max_zoom_image = 2
        self.min_zoom_image = 0.125
        self.zoom_map = 3
        self.max_zoom_map = 18
        self.min_zoom_map = 1
        self.moving = False
        self.first_point=(52.366544, 4.825636)
        self.second_point=(52.363799, 4.832556)

        # create window
        self.window = pygame.display.set_mode(
            self.size, pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE
        )

        # Load OSMCache from osm module
        self.osm = osm.OSMCache("tilecache\\osm", "imagecache\\osm")
        # Load Map coeffecients calculations from Maps module
        self.map_transform = Maps.Map()

        # Fetch initial image for current screen size and zoom level
        # Use Map class to find the correct image input for OSMCache for the current screen size
        initial_bounding_box = self.osm.calculate_bounding_box(self.first_point, self.second_point)
        center, coords, zoom = self.map_transform.best_map_view(initial_bounding_box, self.size[0], self.size[1], 0, 256)
        print(initial_bounding_box, center, coords, zoom)
        self.map, *coords = self.osm.get_combined_image(
            name="home",
            first_point=self.first_point,
            second_point=self.second_point,
            zoom=zoom,
            )
        self.maprect = pygame.Rect(0, 0, self.size[0], self.size[1])

        self.blitmap()





        #currentdir = os.path.dirname(os.path.realpath(__file__))
        #self.map = pygame.image.load(imagedir)
        #self.maprect = self.map.get_rect(center=self.window.get_rect().center)
        #self.blitmap()

        # create window
        pygame.display.flip()

    def blitmap(self):
        self.mapsurface = pygame.transform.smoothscale(self.map, self.maprect.size)
        self.window.fill(0)
        self.window.blit(self.mapsurface, self.maprect)

    def on_init(self):
        self.rtsim = RTSim()

    def on_cleanup(self):
        pygame.quit()

    def check_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False

        elif event.type == pygame.VIDEORESIZE:
            self.window = pygame.display.set_mode(
                event.dict["size"],
                pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.RESIZABLE,
            )
            self.blitmap()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4 or event.button == 5:
                zoom_image = 2 if event.button == 4 else 0.5
                print(self.zoom_image, zoom_image)
                if (
                    self.zoom_image * zoom_image <= self.max_zoom_image
                    and self.zoom_image * zoom_image >= self.min_zoom_image
                ):
                    mx, my = event.pos
                    left = mx + (self.maprect.left - mx) * zoom_image
                    right = mx + (self.maprect.right - mx) * zoom_image
                    top = my + (self.maprect.top - my) * zoom_image
                    bottom = my + (self.maprect.bottom - my) * zoom_image
                    self.maprect = pygame.Rect(left, top, right - left, bottom - top)
                    self.zoom_image = self.zoom_image * zoom_image
                    self.blitmap()
            elif event.button == 1:
                if self.maprect.collidepoint(event.pos):
                    self.moving = True
        elif event.type == MOUSEBUTTONUP:
            if event.button == 1:
                self.moving = False
        elif event.type == MOUSEMOTION and self.moving:
            self.maprect.move_ip(event.rel)
            self.blitmap()

        pygame.display.update()

    def on_execute(self):
        while self.running == True:
            for event in pygame.event.get():
                self.check_event(event)
        self.on_cleanup()


class RTSim(App):
    def __init__(self):
        super().__init__()


start = App()
start.on_init()
start.on_execute()
