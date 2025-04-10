import pygame
import sys
from simulation import Simulation
from visualizer import Visualizer

def main():
    """
    Main entry point for the Universe 25 simulation game.
    """
    # Create simulation with grid size 80x60
    grid_width = 80
    grid_height = 60
    initial_population = 10
    
    simulation = Simulation(grid_width, grid_height, initial_population)
    
    # Create visualizer
    visualizer = Visualizer(simulation)
    
    # Run visualization
    visualizer.run()

if __name__ == "__main__":
    main()
