import pygame

class Runway:
    """Create a Runway object that holds position, length, and width of a runway."""

    def __init__(self, lat, lon, length, width, screen):
        """Initialize a Runway object."""
        self.lat = lat
        self.lon = lon
        self.length = length
        self.width = width
        self.screen = screen
    
    def draw(self):
        """Draw a runway on the screen."""
        # Convert real world coordinates to screen coordinates
        screen_x = self.screen.map.convert_real_to_screen_x(self.lon)
        screen_y = self.screen.map.convert_real_to_screen_y(self.lat)
        # Draw runway
        pygame.draw.rect(
            self.screen.screen,
            (255, 255, 255),
            (screen_x, screen_y, self.length, self.width),
        )