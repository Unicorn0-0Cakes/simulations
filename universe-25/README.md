# Universe 25 Simulation

A simulation game based on John B. Calhoun's famous behavioral experiment from the 1960s-70s that explores how population density affects social behavior in a "mouse utopia" with unlimited resources but limited space.

## About the Experiment

Universe 25 was a real behavioral experiment conducted by ethologist John B. Calhoun. The experiment involved creating a "mouse utopia" - an environment with unlimited food, water, and nesting material, but with physical space constraints. Despite the abundance of resources, the mouse society eventually collapsed due to behavioral changes triggered by increasing population density.

The experiment became a metaphor for:
- Urban overpopulation
- Social alienation
- Psychological deterioration from loss of purpose or structure

## Simulation Features

This simulation recreates the key aspects of the Universe 25 experiment:

- **Environment**: A bounded space with abundant resources
- **Mice Agents**: Individual mice with traits, needs, and behaviors
- **Population Dynamics**: Birth, death, and social interactions
- **Density Effects**: Behavioral changes based on population density
- **Phase Progression**: The four phases observed in the original experiment
  - Exploration & Settlement
  - Rapid Population Growth
  - Social Breakdown
  - Collapse

## How to Run

1. Ensure you have Python 3.6+ installed
2. Install required packages:
   ```
   pip install pygame numpy matplotlib
   ```
3. Run the simulation:
   ```
   python main.py
   ```


---

## 🛠 Optional: Use a Virtual Environment (Recommended)

To isolate dependencies and avoid package conflicts, you can use the included setup script.

### 🧪 To run the script:

1. Save the script below as `setup_env.sh` in your project folder  
2. In Terminal, make it executable:
   ```
   chmod +x setup_env.sh
   ```
3. Then run it:
   ```
   ./setup_env.sh
   ```

This will:
- Install Python 3.10 via `pyenv` (if not already installed)
- Create a virtual environment called `env`
- Install `pygame`, `numpy`, and `matplotlib`

### 🧭 Afterwards:
To reactivate the environment in a new terminal session:
```
source env/bin/activate
```

Want a version tailored for multiple projects, custom Python versions, or named environments? Feel free to ask!


## Controls

- **Pause/Play**: Pause or resume the simulation
- **Speed**: Cycle through simulation speeds (1x, 2x, 5x, 10x, 20x)
- **Reset**: Reset the simulation to initial conditions
- **Mouse Selection**: Click on a mouse to view its detailed information

## Simulation Phases

### Phase 1: Exploration & Settlement
- Small initial population explores the environment
- Healthy social interactions and reproduction
- Balanced territorial behavior

### Phase 2: Rapid Population Growth
- Population increases exponentially
- Social structures form
- Early signs of crowding appear

### Phase 3: Social Breakdown
- Population reaches critical density
- Aggressive behaviors increase
- Maternal neglect rises
- "Beautiful Ones" (withdrawn, well-groomed, non-reproductive mice) begin to appear
- Birth rate starts to decline

### Phase 4: Collapse
- Birth rate plummets
- Social roles dissolve
- Even as population declines, behaviors don't recover
- Population trends toward extinction

## Mouse Behaviors

Mice in the simulation exhibit various behaviors based on their traits and the environment:

- **Normal**: Regular mice with balanced behaviors
- **Aggressors**: Frequently attack others and disrupt social structures
- **Withdrawn/"Beautiful Ones"**: Avoid all social contact, focus on grooming, don't reproduce
- **Neglectful Parents**: Abandon offspring, contributing to population decline

## Statistics and Visualization

The simulation provides real-time statistics and visualizations:

- Population count and density
- Gender and age distribution
- Mental state distribution
- Trait averages (aggression, sociability, parenting, grooming)
- Population graph over time
- Mental state distribution graph

## Educational Value

This simulation can be used to explore concepts such as:
- Population dynamics and carrying capacity
- Effects of overcrowding on social behavior
- The paradox of material abundance without purpose
- Social structures and their breakdown

## Code Structure

- `main.py`: Entry point for the simulation
- `mouse.py`: Defines the Mouse class with behaviors and traits
- `simulation.py`: Manages the environment and population dynamics
- `visualizer.py`: Handles the graphical interface and statistics

## Credits

This simulation is based on John B. Calhoun's Universe 25 experiment, which was conducted at the National Institute of Mental Health (NIMH) from 1968 to 1972.
Gamified by Unicorn0_0Cakes in 2025.

## License

This project is open source and available for educational purposes.
MIT License
