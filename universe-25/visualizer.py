import pygame
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg
from simulation import Simulation
from mouse import Mouse

class Visualizer:
    """
    Handles visualization of the Universe 25 simulation using Pygame.
    """
    
    # Colors
    BACKGROUND_COLOR = (240, 240, 240)
    GRID_COLOR = (200, 200, 200)
    TEXT_COLOR = (0, 0, 0)
    BUTTON_COLOR = (180, 180, 180)
    BUTTON_HOVER_COLOR = (150, 150, 150)
    BUTTON_TEXT_COLOR = (0, 0, 0)
    
    # Phase colors
    PHASE_COLORS = {
        0: (100, 200, 100),  # Exploration - Green
        1: (100, 200, 200),  # Growth - Cyan
        2: (200, 200, 100),  # Breakdown - Yellow
        3: (200, 100, 100)   # Collapse - Red
    }
    
    def __init__(self, simulation, width=1200, height=800, cell_size=8):
        """
        Initialize the visualizer.
        
        Args:
            simulation: Simulation object to visualize
            width (int): Window width
            height (int): Window height
            cell_size (int): Size of each cell in pixels
        """
        self.simulation = simulation
        self.width = width
        self.height = height
        self.cell_size = cell_size
        
        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Universe 25 Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 16)
        self.title_font = pygame.font.SysFont('Arial', 24, bold=True)
        
        # Grid dimensions
        self.grid_width = simulation.width * cell_size
        self.grid_height = simulation.height * cell_size
        self.grid_surface = pygame.Surface((self.grid_width, self.grid_height))
        
        # Stats panel
        self.stats_width = 400
        self.stats_height = self.height
        self.stats_surface = pygame.Surface((self.stats_width, self.stats_height))
        
        # Control panel
        self.control_height = 60
        self.control_width = self.grid_width
        self.control_surface = pygame.Surface((self.control_width, self.control_height))
        
        # Graph dimensions
        self.graph_width = self.stats_width - 20
        self.graph_height = 200
        
        # Buttons
        self.buttons = []
        self._create_buttons()
        
        # Simulation speed
        self.speed = 1  # Updates per frame
        self.paused = False
        
        # Mouse inspection
        self.selected_mouse = None
        
        # Statistics graphs
        self.population_graph = None
        self.state_graph = None
        # Skip initial graph update to avoid errors with empty data
        # self.update_graphs()
    
    def _create_buttons(self):
        """Create control buttons."""
        button_width = 100
        button_height = 30
        padding = 10
        
        # Play/Pause button
        self.buttons.append({
            'rect': pygame.Rect(padding, 15, button_width, button_height),
            'text': 'Pause',
            'action': self.toggle_pause
        })
        
        # Speed buttons
        self.buttons.append({
            'rect': pygame.Rect(padding*2 + button_width, 15, button_width, button_height),
            'text': 'Speed: 1x',
            'action': self.cycle_speed
        })
        
        # Reset button
        self.buttons.append({
            'rect': pygame.Rect(padding*3 + button_width*2, 15, button_width, button_height),
            'text': 'Reset',
            'action': self.reset_simulation
        })
    
    def toggle_pause(self):
        """Toggle simulation pause state."""
        self.paused = not self.paused
        self.buttons[0]['text'] = 'Play' if self.paused else 'Pause'
    
    def cycle_speed(self):
        """Cycle through simulation speeds."""
        speeds = [1, 2, 5, 10, 20]
        current_index = speeds.index(self.speed) if self.speed in speeds else 0
        self.speed = speeds[(current_index + 1) % len(speeds)]
        self.buttons[1]['text'] = f'Speed: {self.speed}x'
    
    def reset_simulation(self):
        """Reset the simulation."""
        width = self.simulation.width
        height = self.simulation.height
        self.simulation = Simulation(width, height, 10)
        self.selected_mouse = None
    
    def update_graphs(self):
        """Update statistical graphs."""
        # Only update graphs every 10 ticks to save performance
        if self.simulation.current_tick % 10 != 0 and self.population_graph is not None:
            return
            
        # Population graph
        if len(self.simulation.population_history) > 1:  # Need at least 2 points to plot
            fig = plt.figure(figsize=(self.graph_width/100, self.graph_height/100), dpi=100)
            ax = fig.add_subplot(111)
            
            # Get data
            ticks = list(range(len(self.simulation.population_history)))
            population = self.simulation.population_history
            
            ax.plot(ticks, population, 'g-')
            ax.set_title('Population')
            ax.set_xlabel('Time')
            ax.set_ylabel('Count')
            ax.grid(True)
            
            # Convert to pygame surface
            canvas = FigureCanvasAgg(fig)
            canvas.draw()
            
            # Get the RGBA buffer and convert to a surface
            w, h = canvas.get_width_height()
            buf = np.frombuffer(canvas.tostring_argb(), dtype=np.uint8)
            buf.shape = (h, w, 4)
            
            # ARGB to RGBA for pygame
            buf = np.roll(buf, 3, axis=2)
            
            # Create pygame surface
            self.population_graph = pygame.image.frombuffer(buf.tobytes(), (w, h), "RGBA")
            plt.close(fig)
        
        # State distribution graph
        if len(self.simulation.state_distribution_history) > 1:
            fig = plt.figure(figsize=(self.graph_width/100, self.graph_height/100), dpi=100)
            ax = fig.add_subplot(111)
            
            # Get data for each state
            state_names = {v: k for k, v in Mouse.STATES.items()}
            data = {state: [] for state in Mouse.STATES.values()}
            
            for dist in self.simulation.state_distribution_history:
                for state, percentage in dist.items():
                    data[state].append(percentage)
            
            # Plot each state
            ticks = list(range(len(self.simulation.state_distribution_history)))
            for state, values in data.items():
                if len(ticks) == len(values):
                    label = state_names[state]
                    ax.plot(ticks, values, label=label)
            
            ax.set_title('Mental States')
            ax.set_xlabel('Time')
            ax.set_ylabel('Percentage')
            ax.legend(loc='upper right', fontsize='small')
            ax.grid(True)
            
            # Convert to pygame surface
            canvas = FigureCanvasAgg(fig)
            canvas.draw()
            
            # Get the RGBA buffer and convert to a surface
            w, h = canvas.get_width_height()
            buf = np.frombuffer(canvas.tostring_argb(), dtype=np.uint8)
            buf.shape = (h, w, 4)
            
            # ARGB to RGBA for pygame
            buf = np.roll(buf, 3, axis=2)
            
            # Create pygame surface
            self.state_graph = pygame.image.frombuffer(buf.tobytes(), (w, h), "RGBA")
            plt.close(fig)
    
    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Check button clicks
                mouse_pos = pygame.mouse.get_pos()
                
                # Adjust for control panel position
                control_pos = (mouse_pos[0], mouse_pos[1] - (self.height - self.control_height))
                
                # Check button clicks
                for button in self.buttons:
                    if button['rect'].collidepoint(control_pos):
                        button['action']()
                
                # Check grid clicks for mouse selection
                if mouse_pos[0] < self.grid_width and mouse_pos[1] < self.grid_height:
                    grid_x = mouse_pos[0] // self.cell_size
                    grid_y = mouse_pos[1] // self.cell_size
                    self.select_mouse_at(grid_x, grid_y)
    
    def select_mouse_at(self, grid_x, grid_y):
        """
        Select a mouse at the given grid position.
        
        Args:
            grid_x (int): Grid X-coordinate
            grid_y (int): Grid Y-coordinate
        """
        for mouse in self.simulation.mice:
            if mouse.x == grid_x and mouse.y == grid_y:
                self.selected_mouse = mouse
                return
        
        # No mouse found at this position
        self.selected_mouse = None
    
    def update(self):
        """Update the visualization."""
        # Handle events
        self.handle_events()
        
        # Update simulation if not paused
        if not self.paused:
            for _ in range(self.speed):
                self.simulation.update()
            
            # Update graphs periodically
            self.update_graphs()
        
        # Draw everything
        self.draw()
        
        # Cap framerate
        self.clock.tick(60)
    
    def draw(self):
        """Draw the visualization."""
        self.screen.fill(self.BACKGROUND_COLOR)
        
        # Draw grid
        self.draw_grid()
        
        # Draw stats panel
        self.draw_stats()
        
        # Draw control panel
        self.draw_controls()
        
        # Update display
        pygame.display.flip()
    
    def draw_grid(self):
        """Draw the simulation grid."""
        self.grid_surface.fill(self.BACKGROUND_COLOR)
        
        # Draw grid lines
        for x in range(0, self.grid_width, self.cell_size):
            pygame.draw.line(self.grid_surface, self.GRID_COLOR, (x, 0), (x, self.grid_height))
        for y in range(0, self.grid_height, self.cell_size):
            pygame.draw.line(self.grid_surface, self.GRID_COLOR, (0, y), (self.grid_width, y))
        
        # Draw mice
        for mouse in self.simulation.mice:
            if mouse.is_alive:
                color = mouse.get_color()
                x = mouse.x * self.cell_size
                y = mouse.y * self.cell_size
                
                # Draw mouse as a circle
                pygame.draw.circle(
                    self.grid_surface, 
                    color, 
                    (x + self.cell_size // 2, y + self.cell_size // 2), 
                    self.cell_size // 2 - 1
                )
                
                # Highlight selected mouse
                if self.selected_mouse is mouse:
                    pygame.draw.circle(
                        self.grid_surface, 
                        (255, 255, 255), 
                        (x + self.cell_size // 2, y + self.cell_size // 2), 
                        self.cell_size // 2, 
                        1
                    )
        
        # Draw grid to screen
        self.screen.blit(self.grid_surface, (0, 0))
    
    def draw_stats(self):
        """Draw the statistics panel."""
        self.stats_surface.fill(self.BACKGROUND_COLOR)
        
        # Get statistics
        stats = self.simulation.get_statistics()
        
        # Draw title
        title = self.title_font.render("Universe 25 Statistics", True, self.TEXT_COLOR)
        self.stats_surface.blit(title, (10, 10))
        
        # Draw phase indicator
        phase_name = stats['phase']
        phase_color = self.PHASE_COLORS[self.simulation.current_phase]
        phase_text = self.title_font.render(f"Phase: {phase_name}", True, phase_color)
        self.stats_surface.blit(phase_text, (10, 40))
        
        # Draw basic stats
        y_pos = 80
        stats_text = [
            f"Tick: {stats['tick']}",
            f"Population: {stats['population']}",
            f"Density: {stats['density_factor']:.2f}",
            f"Males: {stats['gender_ratio']['male']}",
            f"Females: {stats['gender_ratio']['female']}",
            f"Juveniles: {stats['age_groups']['juvenile']}",
            f"Adults: {stats['age_groups']['adult']}",
            f"Deaths: {stats['dead_count']}"
        ]
        
        for text in stats_text:
            surface = self.font.render(text, True, self.TEXT_COLOR)
            self.stats_surface.blit(surface, (10, y_pos))
            y_pos += 20
        
        # Draw trait averages
        y_pos += 10
        self.stats_surface.blit(self.font.render("Average Traits:", True, self.TEXT_COLOR), (10, y_pos))
        y_pos += 20
        
        trait_text = [
            f"Aggression: {stats['avg_traits']['aggression']:.1f}",
            f"Sociability: {stats['avg_traits']['sociability']:.1f}",
            f"Parenting: {stats['avg_traits']['parenting']:.1f}",
            f"Grooming: {stats['avg_traits']['grooming']:.1f}"
        ]
        
        for text in trait_text:
            surface = self.font.render(text, True, self.TEXT_COLOR)
            self.stats_surface.blit(surface, (10, y_pos))
            y_pos += 20
        
        # Draw selected mouse info
        if self.selected_mouse:
            y_pos += 10
            self.stats_surface.blit(self.font.render("Selected Mouse:", True, self.TEXT_COLOR), (10, y_pos))
            y_pos += 20
            
            mouse_info = self.selected_mouse.get_info()
            info_text = [
                f"Age: {mouse_info['age']}",
                f"Gender: {mouse_info['gender']}",
                f"Health: {mouse_info['physical_health']:.1f}",
                f"State: {mouse_info['mental_state']}",
                f"Role: {mouse_info['social_role']}",
                f"Aggression: {mouse_info['aggression']:.1f}",
                f"Sociability: {mouse_info['sociability']:.1f}",
                f"Parenting: {mouse_info['parenting']:.1f}",
                f"Grooming: {mouse_info['grooming']:.1f}",
                f"Children: {mouse_info['children_count']}",
                f"Pregnant: {'Yes' if mouse_info['is_pregnant'] else 'No'}"
            ]
            
            for text in info_text:
                surface = self.font.render(text, True, self.TEXT_COLOR)
                self.stats_surface.blit(surface, (10, y_pos))
                y_pos += 20
        
        # Draw population graph
        if self.population_graph:
            y_pos = max(y_pos + 20, 400)
            self.stats_surface.blit(self.population_graph, (10, y_pos))
            
        # Draw state distribution graph
        if self.state_graph:
            y_pos = max(y_pos + self.graph_height + 10, 620)
            self.stats_surface.blit(self.state_graph, (10, y_pos))
        
        # Draw stats panel to screen
        self.screen.blit(self.stats_surface, (self.grid_width, 0))
    
    def draw_controls(self):
        """Draw the control panel."""
        self.control_surface.fill(self.BACKGROUND_COLOR)
        
        # Draw buttons
        mouse_pos = pygame.mouse.get_pos()
        control_pos = (mouse_pos[0], mouse_pos[1] - (self.height - self.control_height))
        
        for button in self.buttons:
            # Check if mouse is hovering over button
            color = self.BUTTON_HOVER_COLOR if button['rect'].collidepoint(control_pos) else self.BUTTON_COLOR
            
            # Draw button
            pygame.draw.rect(self.control_surface, color, button['rect'])
            pygame.draw.rect(self.control_surface, self.TEXT_COLOR, button['rect'], 1)
            
            # Draw button text
            text = self.font.render(button['text'], True, self.BUTTON_TEXT_COLOR)
            text_rect = text.get_rect(center=button['rect'].center)
            self.control_surface.blit(text, text_rect)
        
        # Draw control panel to screen
        self.screen.blit(self.control_surface, (0, self.height - self.control_height))
    
    def run(self):
        """Run the visualization loop."""
        while True:
            self.update()
