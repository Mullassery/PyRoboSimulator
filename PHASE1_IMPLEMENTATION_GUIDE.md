# Phase 1: Detailed Implementation Guide

## Overview

**Phase 1** expands PyRoboSimulator from single parking lot (Phase 0) to full 2km × 2km procedurally-generated city with traffic, pedestrians, weather, seasons, and streaming.

**Timeline:** 8 weeks  
**Team:** 5 engineers  
**Deliverable:** v0.2.0  
**Starting Point:** Phase 0 complete (36 tests passing, backend stable)  

---

## Week 1-2: Procedural City Generation

### Objectives
1. L-System road generation
2. Voronoi lot subdivision
3. Building placement & height assignment
4. Vegetation distribution
5. POI (Points of Interest) placement
6. City generation testing & reproducibility

### Architecture

**File: `python/pyrobosimulator/city_generator.py`**

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Tuple
import numpy as np
from scipy.spatial import Voronoi, voronoi_plot_2d

class CityStyle(Enum):
    DOWNTOWN = "downtown"
    SUBURBS = "suburbs"
    MIXED = "mixed"

@dataclass
class CitySpec:
    """Complete city specification."""
    id: str
    bounds: Tuple[float, float, float, float]  # (x_min, y_min, x_max, y_max)
    buildings: List['Building']
    roads: List['Road']
    vegetation: List['Tree']
    pois: List['PointOfInterest']
    metadata: Dict

class LSystemRoadGenerator:
    """Generate road network using L-System."""
    
    def __init__(self, seed: int, style: CityStyle):
        self.seed = seed
        self.style = style
        self.np_random = np.random.RandomState(seed)
    
    def generate(self, width: float, height: float) -> List['Road']:
        """Generate road network.
        
        Args:
            width: City width in meters
            height: City height in meters
        
        Returns:
            List of roads
        """
        # 1. Initialize L-System
        axiom = "F[+X][-X]F[-FX][+FX]FX"
        rules = {
            "X": "F-[[X]+X]+F[+FX]-X",
            "F": "F"
        }
        
        # 2. Expand L-System (3-4 iterations)
        sentence = self.expand_lsystem(axiom, rules, iterations=4)
        
        # 3. Interpret as road paths
        roads = self.interpret_roads(sentence, width, height)
        
        # 4. Post-process (smooth curves, snap intersections)
        roads = self.post_process_roads(roads)
        
        return roads
    
    def expand_lsystem(self, axiom: str, rules: Dict[str, str], 
                       iterations: int) -> str:
        """Expand L-System string."""
        current = axiom
        for _ in range(iterations):
            next_str = ""
            for char in current:
                next_str += rules.get(char, char)
            current = next_str
        return current
    
    def interpret_roads(self, sentence: str, width: float, 
                       height: float) -> List['Road']:
        """Convert L-System string to road paths.
        
        Rules:
        - F: Draw forward (create road segment)
        - +: Turn right 45°
        - -: Turn left 45°
        - [: Push position/rotation state
        - ]: Pop position/rotation state
        """
        roads = []
        x, y = width / 2, height / 2
        angle = 90  # Start pointing north
        
        stack = []  # (x, y, angle)
        segment_id = 0
        
        for char in sentence:
            if char == 'F':
                # Draw road segment
                dx = np.cos(np.radians(angle)) * 50  # 50m segments
                dy = np.sin(np.radians(angle)) * 50
                
                next_x, next_y = x + dx, y + dy
                
                # Clamp to bounds
                next_x = np.clip(next_x, 0, width)
                next_y = np.clip(next_y, 0, height)
                
                road = Road(
                    id=f"road_{segment_id}",
                    start=(x, y),
                    end=(next_x, next_y),
                    width=self.get_road_width(angle),
                    type=self.get_road_type(len(stack)),
                )
                roads.append(road)
                segment_id += 1
                
                x, y = next_x, next_y
            
            elif char == '+':
                angle -= 45
            elif char == '-':
                angle += 45
            elif char == '[':
                stack.append((x, y, angle))
            elif char == ']':
                if stack:
                    x, y, angle = stack.pop()
        
        return roads
    
    def get_road_width(self, angle: float) -> float:
        """Determine road width based on hierarchy."""
        # Horizontal/vertical roads (highways): 20m
        # Diagonal roads (arterial): 15m
        return 20.0 if (angle % 90 == 0) else 15.0
    
    def get_road_type(self, hierarchy_level: int) -> str:
        """Determine road type by hierarchy."""
        if hierarchy_level == 0:
            return "highway"
        elif hierarchy_level == 1:
            return "arterial"
        else:
            return "local"
    
    def post_process_roads(self, roads: List['Road']) -> List['Road']:
        """Clean up road network."""
        # 1. Merge adjacent segments
        # 2. Remove dead ends <100m
        # 3. Snap intersections
        # 4. Add traffic lights at major intersections
        return roads

@dataclass
class Road:
    id: str
    start: Tuple[float, float]
    end: Tuple[float, float]
    width: float
    type: str  # highway, arterial, local
    traffic_lanes: int = 2
    has_traffic_light: bool = False

class VoronoiLotSubdivider:
    """Divide city blocks into lots using Voronoi."""
    
    def __init__(self, seed: int):
        self.seed = seed
        self.np_random = np.random.RandomState(seed)
    
    def subdivide_block(self, block_polygon: List[Tuple[float, float]],
                       density: float = 0.8) -> List['Lot']:
        """Divide block into building lots.
        
        Args:
            block_polygon: Block boundary (4 corners for rectangular blocks)
            density: 0-1, how many lots fill the block
        
        Returns:
            List of building lots
        """
        # 1. Generate random points (Poisson disk sampling)
        x_min, y_min = min(p[0] for p in block_polygon), min(p[1] for p in block_polygon)
        x_max, y_max = max(p[0] for p in block_polygon), max(p[1] for p in block_polygon)
        
        num_points = int((x_max - x_min) * (y_max - y_min) * density / (100 * 100))
        points = self.generate_poisson_points(
            x_min, y_min, x_max, y_max, num_points
        )
        
        # 2. Compute Voronoi diagram
        vor = Voronoi(points)
        
        # 3. Extract lots (clipped to block boundary)
        lots = []
        for i, region in enumerate(vor.regions):
            if len(region) > 0 and -1 not in region:
                vertices = vor.vertices[region]
                lot_polygon = self.clip_polygon(vertices, block_polygon)
                
                if len(lot_polygon) > 2:
                    lot = Lot(
                        id=f"lot_{i}",
                        polygon=lot_polygon,
                        block_id=None  # Will be set later
                    )
                    lots.append(lot)
        
        return lots
    
    def generate_poisson_points(self, x_min: float, y_min: float,
                                x_max: float, y_max: float, 
                                num_points: int) -> np.ndarray:
        """Generate Poisson disk sampled points."""
        # Simplified: just random + rejection
        points = []
        min_distance = np.sqrt((x_max - x_min) * (y_max - y_min) / num_points)
        
        for _ in range(num_points * 10):  # Try multiple times
            x = self.np_random.uniform(x_min, x_max)
            y = self.np_random.uniform(y_min, y_max)
            
            # Check distance to existing points
            valid = True
            for px, py in points:
                if np.sqrt((x - px)**2 + (y - py)**2) < min_distance:
                    valid = False
                    break
            
            if valid:
                points.append([x, y])
        
        return np.array(points)
    
    def clip_polygon(self, vertices: np.ndarray,
                     clip_polygon: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Clip Voronoi polygon to block boundary using Sutherland-Hodgman."""
        # Simplified clipping
        return [(v[0], v[1]) for v in vertices if self.point_in_polygon(v, clip_polygon)]
    
    def point_in_polygon(self, point: np.ndarray, 
                        polygon: List[Tuple[float, float]]) -> bool:
        """Check if point is inside polygon (ray casting)."""
        x, y = point
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y
        
        return inside

@dataclass
class Lot:
    id: str
    polygon: List[Tuple[float, float]]
    block_id: str

class BuildingGenerator:
    """Generate buildings from lots."""
    
    def __init__(self, seed: int, style: CityStyle):
        self.seed = seed
        self.style = style
        self.np_random = np.random.RandomState(seed)
    
    def generate_building(self, lot: Lot) -> 'Building':
        """Generate building on lot.
        
        Decisions:
        1. Building height (zoning rules)
        2. Footprint (setback from lot edges)
        3. Type (residential, commercial, etc.)
        4. Material/color
        5. Windows pattern
        """
        # 1. Compute lot center & size
        polygon = np.array(lot.polygon)
        center_x = np.mean(polygon[:, 0])
        center_y = np.mean(polygon[:, 1])
        area = self.polygon_area(polygon)
        
        # 2. Determine building type by zoning (style-dependent)
        building_type = self.choose_building_type(area)
        
        # 3. Determine height
        height = self.get_building_height(building_type)
        
        # 4. Apply setback (10-20% from edges)
        setback = self.np_random.uniform(0.1, 0.2)
        footprint = self.apply_setback(polygon, setback)
        
        # 5. Assign material/color
        color_variance = self.np_random.uniform(0, 1)
        
        building = Building(
            id=f"building_{lot.id}",
            lot_id=lot.id,
            position=(center_x, center_y),
            height=height,
            footprint=footprint,
            type=building_type,
            color_variance=color_variance,
            windows_pattern=self.choose_windows_pattern(building_type),
            roof_type=self.choose_roof_type(building_type),
        )
        
        return building
    
    def polygon_area(self, polygon: np.ndarray) -> float:
        """Compute polygon area using Shoelace formula."""
        x = polygon[:, 0]
        y = polygon[:, 1]
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    
    def choose_building_type(self, area: float) -> str:
        """Choose building type by area & style."""
        if self.style == CityStyle.DOWNTOWN:
            # Downtown: mix of commercial & high-rise
            if area < 500:
                return self.np_random.choice(
                    ["commercial", "residential_mid"],
                    p=[0.7, 0.3]
                )
            else:
                return "residential_high"
        else:
            # Suburbs: mostly residential
            return self.np_random.choice(
                ["residential_low", "residential_mid"],
                p=[0.7, 0.3]
            )
    
    def get_building_height(self, building_type: str) -> float:
        """Get building height by type."""
        height_map = {
            "residential_low": self.np_random.uniform(6, 12),      # 2-4 stories
            "residential_mid": self.np_random.uniform(15, 25),     # 5-8 stories
            "residential_high": self.np_random.uniform(30, 80),    # 10-25 stories
            "commercial": self.np_random.uniform(20, 60),          # 6-18 stories
            "industrial": self.np_random.uniform(8, 15),           # 1-4 stories
            "landmark": self.np_random.uniform(50, 150),           # 15-50 stories
        }
        return height_map.get(building_type, 20.0)
    
    def apply_setback(self, polygon: np.ndarray, 
                     setback_ratio: float) -> List[Tuple[float, float]]:
        """Shrink polygon inward by setback."""
        # Simplified: just scale from center
        center = polygon.mean(axis=0)
        shrunk = polygon + (center - polygon) * setback_ratio
        return [(p[0], p[1]) for p in shrunk]
    
    def choose_windows_pattern(self, building_type: str) -> str:
        """Choose window pattern."""
        patterns = {
            "residential": ["grid", "modern"],
            "commercial": ["modern", "ornate"],
            "landmark": ["ornate"],
        }
        category = "residential" if "residential" in building_type else \
                   "commercial" if "commercial" in building_type else "landmark"
        return self.np_random.choice(patterns.get(category, ["grid"]))
    
    def choose_roof_type(self, building_type: str) -> str:
        """Choose roof type."""
        if "residential" in building_type and "high" not in building_type:
            return self.np_random.choice(["pitched", "flat"], p=[0.6, 0.4])
        else:
            return "flat"

@dataclass
class Building:
    id: str
    lot_id: str
    position: Tuple[float, float]
    height: float
    footprint: List[Tuple[float, float]]
    type: str
    color_variance: float
    windows_pattern: str
    roof_type: str
```

### Testing (Week 1-2)

```python
# tests/test_city_generator.py
class TestCityGeneration:
    def test_lsystem_reproducibility(self):
        """Same seed → same city."""
        gen1 = LSystemRoadGenerator(seed=42, style=CityStyle.DOWNTOWN)
        gen2 = LSystemRoadGenerator(seed=42, style=CityStyle.DOWNTOWN)
        
        roads1 = gen1.generate(2000, 2000)
        roads2 = gen2.generate(2000, 2000)
        
        assert len(roads1) == len(roads2)
        for r1, r2 in zip(roads1, roads2):
            assert r1.start == r2.start
            assert r1.end == r2.end
    
    def test_building_count(self):
        """Reasonable building count for 2km × 2km city."""
        generator = CityGenerator(seed=42, style=CityStyle.DOWNTOWN)
        city = generator.generate(2000, 2000)
        
        assert 40000 < len(city.buildings) < 60000
    
    def test_city_bounds(self):
        """All buildings within city bounds."""
        generator = CityGenerator(seed=42, style=CityStyle.MIXED)
        city = generator.generate(2000, 2000)
        
        for building in city.buildings:
            x, y = building.position
            assert 0 <= x <= 2000
            assert 0 <= y <= 2000
    
    def test_road_connectivity(self):
        """Roads form connected network."""
        generator = CityGenerator(seed=42, style=CityStyle.SUBURBS)
        city = generator.generate(2000, 2000)
        
        # Build adjacency graph
        graph = {}
        for road in city.roads:
            start = road.start
            end = road.end
            if start not in graph:
                graph[start] = []
            if end not in graph:
                graph[end] = []
            graph[start].append(end)
            graph[end].append(start)
        
        # Check connectivity via BFS
        if graph:
            visited = set()
            queue = [list(graph.keys())[0]]
            while queue:
                node = queue.pop(0)
                if node not in visited:
                    visited.add(node)
                    queue.extend(graph.get(node, []))
            
            # All nodes should be reachable from first node
            assert len(visited) > len(graph) * 0.8  # 80% connected
```

### API Integration (Week 2)

**Add to `python/pyrobosimulator/api.py`:**

```python
from .city_generator import CityGenerator, CityStyle

@app.post("/api/v1/cities/generate")
async def generate_city(request: CityGenerationRequest) -> CityGenerationResponse:
    """Generate procedural city.
    
    Args:
        seed: Random seed (reproducible)
        style: "downtown", "suburbs", or "mixed"
        size_km: City size (1-5 km)
        building_density: 0-1 (how full)
    """
    try:
        generator = CityGenerator(
            seed=request.seed,
            style=CityStyle(request.style)
        )
        
        size_m = request.size_km * 1000
        city = generator.generate(size_m, size_m)
        
        # Save to database
        city_id = save_city_to_db(city)
        
        return CityGenerationResponse(
            city_id=city_id,
            building_count=len(city.buildings),
            road_length_km=sum(r.length for r in city.roads) / 1000,
            generated_at=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"City generation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
```

---

## Week 3-4: Traffic Simulation

### Objectives
1. Road network graph construction
2. Vehicle pathfinding (A*)
3. Vehicle physics (acceleration, braking)
4. Lane changing behavior
5. Collision avoidance
6. Traffic density control

### Architecture

**File: `python/pyrobosimulator/traffic_system.py`**

```python
import heapq
from dataclasses import dataclass
from typing import List, Dict, Set, Optional

class TrafficSimulator:
    """Simulate vehicular traffic on road network."""
    
    def __init__(self, city_spec: CitySpec):
        self.roads = city_spec.roads
        self.graph = self.build_road_graph()
        self.vehicles: List[Vehicle] = []
        self.intersections = self.find_intersections()
        self.dt = 0.01  # 10ms timestep
        self.spawn_queue = []
    
    def build_road_graph(self) -> Dict:
        """Build adjacency graph for pathfinding."""
        graph = {}
        for road in self.roads:
            start = road.start
            end = road.end
            if start not in graph:
                graph[start] = []
            if end not in graph:
                graph[end] = []
            
            # Store both directions for undirected graph
            graph[start].append({
                'neighbor': end,
                'road': road,
                'distance': self.distance(start, end)
            })
            graph[end].append({
                'neighbor': start,
                'road': road,
                'distance': self.distance(start, end)
            })
        
        return graph
    
    def find_intersections(self) -> List['Intersection']:
        """Find where roads meet."""
        intersections = []
        position_counts = {}
        
        for road in self.roads:
            for pos in [road.start, road.end]:
                key = (round(pos[0], 1), round(pos[1], 1))
                if key not in position_counts:
                    position_counts[key] = []
                position_counts[key].append(road)
        
        for pos, roads in position_counts.items():
            if len(roads) > 1:
                intersection = Intersection(
                    position=pos,
                    roads=roads,
                    traffic_light=len(roads) > 2  # Traffic light at 3+ way
                )
                intersections.append(intersection)
        
        return intersections
    
    def spawn_vehicle(self, start_pos: Tuple[float, float],
                     end_pos: Tuple[float, float],
                     vehicle_type: str = "car") -> bool:
        """Spawn vehicle with destination.
        
        Returns:
            True if spawned successfully, False if no valid path
        """
        # Find path
        path = self.find_path(start_pos, end_pos)
        if not path:
            return False
        
        vehicle = Vehicle(
            id=f"vehicle_{len(self.vehicles)}",
            start=start_pos,
            destination=end_pos,
            path=path,
            vehicle_type=vehicle_type,
            speed=self.get_max_speed(vehicle_type)
        )
        
        self.vehicles.append(vehicle)
        return True
    
    def find_path(self, start: Tuple[float, float],
                 end: Tuple[float, float]) -> Optional[List[Tuple[float, float]]]:
        """Find shortest path using A*."""
        
        def heuristic(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
            return self.distance(pos1, pos2)
        
        # Find nearest graph nodes
        start_node = self.find_nearest_node(start)
        end_node = self.find_nearest_node(end)
        
        if not start_node or not end_node:
            return None
        
        # A* algorithm
        open_set = [(0, start_node)]
        came_from = {}
        g_score = {start_node: 0}
        f_score = {start_node: heuristic(start_node, end_node)}
        closed_set = set()
        
        while open_set:
            _, current = heapq.heappop(open_set)
            
            if current == end_node:
                # Reconstruct path
                path = []
                node = current
                while node in came_from:
                    path.append(node)
                    node = came_from[node]
                path.append(start_node)
                path.reverse()
                return path
            
            closed_set.add(current)
            
            for neighbor_info in self.graph.get(current, []):
                neighbor = neighbor_info['neighbor']
                distance = neighbor_info['distance']
                
                if neighbor in closed_set:
                    continue
                
                tentative_g = g_score[current] + distance
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, end_node)
                    
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return None
    
    def find_nearest_node(self, pos: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """Find nearest graph node to position."""
        if not self.graph:
            return None
        
        nearest = min(self.graph.keys(),
                     key=lambda node: self.distance(pos, node))
        return nearest
    
    def distance(self, pos1: Tuple[float, float],
                pos2: Tuple[float, float]) -> float:
        """Euclidean distance."""
        return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
    
    def update(self, dt: float):
        """Simulate traffic for dt seconds."""
        
        # Update each vehicle
        for vehicle in self.vehicles:
            self.update_vehicle(vehicle, dt)
        
        # Remove arrived vehicles
        self.vehicles = [v for v in self.vehicles if not v.arrived]
    
    def update_vehicle(self, vehicle: Vehicle, dt: float):
        """Update single vehicle."""
        
        if vehicle.arrived:
            return
        
        # 1. Get target from path
        if vehicle.current_waypoint_idx >= len(vehicle.path):
            vehicle.arrived = True
            return
        
        target = vehicle.path[vehicle.current_waypoint_idx]
        
        # 2. Compute desired velocity
        to_target = (target[0] - vehicle.x, target[1] - vehicle.y)
        dist_to_target = np.sqrt(to_target[0]**2 + to_target[1]**2)
        
        if dist_to_target < 10:  # Waypoint reached
            vehicle.current_waypoint_idx += 1
            return
        
        # Normalize direction
        direction = (to_target[0] / dist_to_target, to_target[1] / dist_to_target)
        desired_velocity = (direction[0] * vehicle.speed, 
                           direction[1] * vehicle.speed)
        
        # 3. Collision avoidance (simple: check nearby vehicles)
        nearby = self.find_nearby_vehicles(vehicle, radius=20)
        if nearby:
            # Adjust velocity to avoid collision
            avoidance_vector = self.compute_avoidance_vector(vehicle, nearby)
            desired_velocity = (
                desired_velocity[0] * 0.7 + avoidance_vector[0] * 0.3,
                desired_velocity[1] * 0.7 + avoidance_vector[1] * 0.3
            )
        
        # 4. Apply physics (smooth acceleration)
        max_accel = 5.0  # m/s^2
        dvx = max(min(desired_velocity[0] - vehicle.vx, max_accel * dt), -max_accel * dt)
        dvy = max(min(desired_velocity[1] - vehicle.vy, max_accel * dt), -max_accel * dt)
        
        vehicle.vx += dvx
        vehicle.vy += dvy
        
        # 5. Update position
        vehicle.x += vehicle.vx * dt
        vehicle.y += vehicle.vy * dt
    
    def find_nearby_vehicles(self, vehicle: Vehicle, 
                            radius: float) -> List[Vehicle]:
        """Find vehicles within radius."""
        nearby = []
        for other in self.vehicles:
            if other.id != vehicle.id:
                dist = self.distance((vehicle.x, vehicle.y), 
                                    (other.x, other.y))
                if dist < radius:
                    nearby.append(other)
        return nearby
    
    def compute_avoidance_vector(self, vehicle: Vehicle,
                                nearby: List[Vehicle]) -> Tuple[float, float]:
        """Compute vector pointing away from nearby vehicles."""
        avoidance = [0.0, 0.0]
        for other in nearby:
            dx = vehicle.x - other.x
            dy = vehicle.y - other.y
            dist = np.sqrt(dx**2 + dy**2)
            if dist > 0:
                avoidance[0] += dx / (dist**2 + 0.1)
                avoidance[1] += dy / (dist**2 + 0.1)
        
        mag = np.sqrt(avoidance[0]**2 + avoidance[1]**2)
        if mag > 0:
            return (avoidance[0] / mag, avoidance[1] / mag)
        return (0, 0)
    
    def get_max_speed(self, vehicle_type: str) -> float:
        """Get max speed by vehicle type."""
        speeds = {
            "car": 15,        # 54 km/h
            "truck": 12,      # 43 km/h
            "bus": 12,
            "taxi": 15,
            "motorcycle": 18, # 65 km/h
            "bicycle": 6,     # 22 km/h
        }
        return speeds.get(vehicle_type, 10)
    
    def set_traffic_density(self, level: float):
        """Control traffic density (0-1)."""
        # level=0: 1 vehicle every 10 seconds
        # level=0.5: 1 vehicle every 5 seconds
        # level=1.0: 1 vehicle every 2 seconds
        self.spawn_rate = 1.0 / (10 - 8 * level)  # vehicles/second

@dataclass
class Vehicle:
    id: str
    start: Tuple[float, float]
    destination: Tuple[float, float]
    path: List[Tuple[float, float]]
    vehicle_type: str
    speed: float
    
    # State
    x: float = 0
    y: float = 0
    vx: float = 0
    vy: float = 0
    current_waypoint_idx: int = 0
    arrived: bool = False
    
    def __post_init__(self):
        self.x, self.y = self.start

@dataclass
class Intersection:
    position: Tuple[float, float]
    roads: List['Road']
    traffic_light: bool = False
    light_state: str = "red"  # red, green
    light_duration: float = 30.0  # seconds
```

### Testing (Week 3-4)

```python
# tests/test_traffic.py
class TestTrafficSimulation:
    def test_vehicle_pathfinding(self):
        """Vehicle finds path from start to destination."""
        city = create_test_city()
        simulator = TrafficSimulator(city)
        
        start = city.roads[0].start
        end = city.roads[-1].end
        
        success = simulator.spawn_vehicle(start, end)
        assert success
        assert len(simulator.vehicles) == 1
    
    def test_collision_avoidance(self):
        """Vehicles avoid collisions."""
        city = create_test_city()
        simulator = TrafficSimulator(city)
        
        # Spawn two vehicles on collision course
        simulator.spawn_vehicle((0, 0), (100, 100))
        simulator.spawn_vehicle((100, 100), (0, 0))
        
        # Simulate
        for _ in range(1000):
            simulator.update(0.01)
        
        # Check no collision
        for v1 in simulator.vehicles:
            for v2 in simulator.vehicles:
                if v1.id != v2.id:
                    dist = simulator.distance(
                        (v1.x, v1.y), (v2.x, v2.y)
                    )
                    assert dist > 2  # Minimum safe distance
    
    def test_traffic_density_control(self):
        """Traffic density affects spawn rate."""
        city = create_test_city()
        simulator = TrafficSimulator(city)
        
        simulator.set_traffic_density(0.0)  # Very light
        initial_rate = simulator.spawn_rate
        
        simulator.set_traffic_density(1.0)  # Very heavy
        heavy_rate = simulator.spawn_rate
        
        assert heavy_rate > initial_rate
```

---

## Week 4-5: Pedestrian AI

### Key Algorithms
- Pathfinding (A* on sidewalk network)
- Social force model (crowd simulation)
- Grouping & hierarchy
- Destination selection (random vs. POI)

**File: `python/pyrobosimulator/pedestrian_system.py`**

```python
class PedestrianSimulator:
    """Simulate pedestrian movement with social forces."""
    
    def __init__(self, city_spec: CitySpec):
        self.sidewalk_network = self.extract_sidewalk_network(city_spec)
        self.pois = city_spec.pois
        self.pedestrians: List[Pedestrian] = []
        self.groups: Dict[str, PedestrianGroup] = {}
    
    def spawn_pedestrian(self, start_pos: Tuple[float, float],
                        group_id: Optional[str] = None) -> 'Pedestrian':
        """Spawn pedestrian with random destination."""
        
        # Choose destination
        if np.random.random() < 0.3:
            # Go to POI
            destination = self.choose_poi()
        else:
            # Random location
            destination = self.random_location()
        
        # Find path
        path = self.find_sidewalk_path(start_pos, destination)
        
        # Personality
        speed = np.random.normal(1.4, 0.3)  # Average 1.4 m/s
        speed = np.clip(speed, 0.5, 2.0)
        
        ped = Pedestrian(
            id=f"ped_{len(self.pedestrians)}",
            position=list(start_pos),
            destination=destination,
            path=path,
            speed=speed,
            group_id=group_id,
        )
        
        self.pedestrians.append(ped)
        
        # Add to group if specified
        if group_id:
            if group_id not in self.groups:
                self.groups[group_id] = PedestrianGroup(group_id)
            self.groups[group_id].members.append(ped.id)
        
        return ped
    
    def update(self, dt: float):
        """Update pedestrian positions."""
        
        for ped in self.pedestrians:
            self.update_pedestrian(ped, dt)
        
        # Remove arrived pedestrians
        self.pedestrians = [p for p in self.pedestrians if not p.arrived]
    
    def update_pedestrian(self, ped: Pedestrian, dt: float):
        """Update single pedestrian using social force model."""
        
        if ped.arrived:
            return
        
        # 1. Goal force (toward destination)
        goal_force = self.compute_goal_force(ped)
        
        # 2. Social force (repulsion from other pedestrians)
        social_force = self.compute_social_force(ped)
        
        # 3. Group force (attraction to group members)
        group_force = self.compute_group_force(ped)
        
        # 4. Wall force (avoid obstacles)
        wall_force = self.compute_wall_force(ped)
        
        # Combine forces (weighted)
        total_force = (
            2.0 * goal_force +
            1.0 * social_force +
            0.5 * group_force +
            1.5 * wall_force
        )
        
        # Update velocity
        mass = 80  # kg
        acceleration = (total_force[0] / mass, total_force[1] / mass)
        
        ped.velocity[0] += acceleration[0] * dt
        ped.velocity[1] += acceleration[1] * dt
        
        # Cap speed
        speed = np.sqrt(ped.velocity[0]**2 + ped.velocity[1]**2)
        if speed > ped.speed:
            scale = ped.speed / speed
            ped.velocity[0] *= scale
            ped.velocity[1] *= scale
        
        # Update position
        ped.position[0] += ped.velocity[0] * dt
        ped.position[1] += ped.velocity[1] * dt
        
        # Check if reached destination
        dist_to_dest = np.sqrt(
            (ped.position[0] - ped.destination[0])**2 +
            (ped.position[1] - ped.destination[1])**2
        )
        if dist_to_dest < 2:
            ped.arrived = True
    
    def compute_goal_force(self, ped: Pedestrian) -> Tuple[float, float]:
        """Force pulling pedestrian toward destination."""
        
        if ped.current_waypoint_idx >= len(ped.path):
            target = ped.destination
        else:
            target = ped.path[ped.current_waypoint_idx]
        
        dx = target[0] - ped.position[0]
        dy = target[1] - ped.position[1]
        dist = np.sqrt(dx**2 + dy**2)
        
        if dist < 1:  # Reached waypoint
            ped.current_waypoint_idx += 1
            return (0, 0)
        
        # Desired velocity toward target
        desired_v = (dx / dist * ped.speed, dy / dist * ped.speed)
        
        # Force = (desired - actual) / tau
        tau = 0.5  # Relaxation time
        force_x = (desired_v[0] - ped.velocity[0]) / tau
        force_y = (desired_v[1] - ped.velocity[1]) / tau
        
        return (force_x, force_y)
    
    def compute_social_force(self, ped: Pedestrian) -> Tuple[float, float]:
        """Repulsive force from other pedestrians."""
        
        force_x, force_y = 0, 0
        
        for other in self.pedestrians:
            if other.id == ped.id:
                continue
            
            dx = ped.position[0] - other.position[0]
            dy = ped.position[1] - other.position[1]
            dist = np.sqrt(dx**2 + dy**2)
            
            if dist < 0.1:
                dist = 0.1
            
            # Repulsive force (inverse square)
            A = 2000  # Amplitude
            B = 0.08  # Characteristic distance
            
            magnitude = A * np.exp(-dist / B) / (dist + 0.1)
            
            if dist > 0:
                force_x += magnitude * dx / dist
                force_y += magnitude * dy / dist
        
        return (force_x, force_y)
    
    def compute_group_force(self, ped: Pedestrian) -> Tuple[float, float]:
        """Attraction force toward group members."""
        
        if not ped.group_id:
            return (0, 0)
        
        group = self.groups.get(ped.group_id)
        if not group:
            return (0, 0)
        
        # Average position of group members
        group_x = 0
        group_y = 0
        count = 0
        
        for member_id in group.members:
            for other in self.pedestrians:
                if other.id == member_id:
                    group_x += other.position[0]
                    group_y += other.position[1]
                    count += 1
        
        if count == 0:
            return (0, 0)
        
        group_center = (group_x / count, group_y / count)
        
        # Small attractive force to stay near group
        dx = group_center[0] - ped.position[0]
        dy = group_center[1] - ped.position[1]
        
        return (dx * 0.1, dy * 0.1)
    
    def compute_wall_force(self, ped: Pedestrian) -> Tuple[float, float]:
        """Repulsive force from obstacles."""
        
        # Check distance to buildings
        force_x, force_y = 0, 0
        
        for building in self.buildings:
            # Distance to building
            dist = self.distance_to_polygon(
                ped.position, building.footprint
            )
            
            if dist < 5:  # Within 5m
                # Repulsive force
                direction = self.direction_away_from_building(
                    ped.position, building.footprint
                )
                magnitude = max(0, 1 - dist / 5) * 500
                force_x += magnitude * direction[0]
                force_y += magnitude * direction[1]
        
        return (force_x, force_y)

@dataclass
class Pedestrian:
    id: str
    position: List[float]
    destination: Tuple[float, float]
    path: List[Tuple[float, float]]
    speed: float
    group_id: Optional[str] = None
    
    # State
    velocity: List[float] = None
    current_waypoint_idx: int = 0
    arrived: bool = False
    
    def __post_init__(self):
        if self.velocity is None:
            self.velocity = [0, 0]

@dataclass
class PedestrianGroup:
    id: str
    members: List[str] = None
    
    def __post_init__(self):
        if self.members is None:
            self.members = []
```

---

## Week 5: Weather & Seasons

**Timeline:** 1 week (fast integration of Phase 0 weather specs)

### Implementation

**File: `python/pyrobosimulator/weather_system.py`**

```python
class WeatherSystem:
    """Dynamic weather and seasonal system."""
    
    def __init__(self, city_spec: CitySpec):
        self.current_time = 0  # Seconds since start
        self.weather_state = "clear"
        self.rain_intensity = 0
        self.cloud_coverage = 0
        self.wind_speed = 0
        self.temperature = 20  # °C
    
    def update(self, dt: float, game_time: float):
        """Update weather (game_time in hours, 0-365)."""
        
        self.current_time += dt
        
        # Update weather smoothly
        self.update_weather()
        
        # Update seasonal parameters
        self.update_season(game_time)
    
    def update_weather(self):
        """Smooth weather transitions."""
        
        # Use Perlin noise for weather (generates natural variation)
        noise_val = self.perlin_noise(self.current_time / 300)  # ~5min cycle
        
        if noise_val < -0.7:
            new_state = "thunderstorm"
            target_rain = 1.0
            target_clouds = 1.0
            target_wind = 15
        elif noise_val < -0.3:
            new_state = "heavy_rain"
            target_rain = 0.8
            target_clouds = 1.0
            target_wind = 10
        elif noise_val < 0.2:
            new_state = "light_rain"
            target_rain = 0.3
            target_clouds = 0.7
            target_wind = 3
        elif noise_val < 0.5:
            new_state = "partly_cloudy"
            target_rain = 0
            target_clouds = 0.5
            target_wind = 2
        else:
            new_state = "clear"
            target_rain = 0
            target_clouds = 0
            target_wind = 0
        
        # Smooth interpolation (5-30 minute transitions)
        alpha = 0.01  # Smooth factor
        self.rain_intensity += (target_rain - self.rain_intensity) * alpha
        self.cloud_coverage += (target_clouds - self.cloud_coverage) * alpha
        self.wind_speed += (target_wind - self.wind_speed) * alpha
        
        self.weather_state = new_state
    
    def update_season(self, hour_of_day: float):
        """Update seasonal and time-of-day effects."""
        
        # Temperature variation
        day_of_year = int(hour_of_day) % 365
        season = self.get_season(day_of_year)
        
        # Base temp by season
        season_temps = {
            "winter": 5,
            "spring": 15,
            "summer": 25,
            "fall": 15,
        }
        base_temp = season_temps[season]
        
        # Diurnal variation (±5°C)
        hour_of_day_mod = hour_of_day % 24
        diurnal = 5 * np.sin(2 * np.pi * (hour_of_day_mod - 6) / 24)
        
        self.temperature = base_temp + diurnal
    
    def get_season(self, day_of_year: int) -> str:
        """Get season from day of year."""
        if day_of_year < 90:
            return "winter"
        elif day_of_year < 180:
            return "spring"
        elif day_of_year < 270:
            return "summer"
        else:
            return "fall"
    
    def get_seasonal_color_shift(self, day_of_year: int) -> Dict[str, float]:
        """Get color shift for vegetation by season."""
        season = self.get_season(day_of_year)
        
        shifts = {
            "spring": {"hue": 0.2, "saturation": 0.3},
            "summer": {"hue": 0.0, "saturation": 0.0},
            "fall": {"hue": 0.8, "saturation": -0.2},
            "winter": {"hue": -0.2, "saturation": -0.5},
        }
        
        return shifts.get(season, {})
```

---

## Week 6-7: Streaming & Persistence

### Chunking System

**File: `python/pyrobosimulator/streaming.py`**

```python
class StreamingManager:
    """Load/unload city chunks dynamically."""
    
    def __init__(self, city_spec: CitySpec):
        self.chunks = self.partition_city(city_spec)
        self.loaded_chunks = {}
        self.camera_position = (0, 0)
        self.chunk_size = 500  # 500m × 500m
    
    def update_viewport(self, camera_x: float, camera_y: float):
        """Update loaded chunks based on camera position."""
        
        self.camera_position = (camera_x, camera_y)
        
        # Find current chunk
        current_chunk_idx = self.get_chunk_at(camera_x, camera_y)
        
        # Always load current + adjacent (3×3 grid)
        to_load = self.get_adjacent_chunks(current_chunk_idx, radius=1)
        
        # Load new chunks
        for chunk_idx in to_load:
            if chunk_idx not in self.loaded_chunks:
                self.load_chunk(chunk_idx)
        
        # Unload far chunks
        to_unload = []
        for chunk_idx in self.loaded_chunks:
            if self.distance_between_chunks(chunk_idx, current_chunk_idx) > 2:
                to_unload.append(chunk_idx)
        
        for chunk_idx in to_unload:
            self.unload_chunk(chunk_idx)
    
    def load_chunk(self, chunk_idx: int):
        """Load chunk (blocking)."""
        chunk = self.chunks[chunk_idx]
        
        # Load building meshes
        for building in chunk.buildings:
            self.load_building_assets(building)
        
        # Load vegetation
        for tree in chunk.vegetation:
            self.load_tree_assets(tree)
        
        self.loaded_chunks[chunk_idx] = chunk
        logger.info(f"Loaded chunk {chunk_idx}")
    
    def unload_chunk(self, chunk_idx: int):
        """Unload chunk (free memory)."""
        chunk = self.loaded_chunks.pop(chunk_idx)
        self.free_chunk_assets(chunk)
        logger.info(f"Unloaded chunk {chunk_idx}")
```

### Database Schema (PostgreSQL)

```sql
-- Cities
CREATE TABLE cities (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    seed INT,
    style VARCHAR(50),
    size_km FLOAT,
    created_at TIMESTAMP,
    metadata JSONB
);

-- Buildings
CREATE TABLE buildings (
    id UUID PRIMARY KEY,
    city_id UUID REFERENCES cities ON DELETE CASCADE,
    position GEOMETRY(Point),
    height FLOAT,
    type VARCHAR(50),
    footprint GEOMETRY(Polygon),
    color_variance FLOAT,
    windows_pattern VARCHAR(50),
    roof_type VARCHAR(50),
    INDEX building_city (city_id),
    INDEX building_position (position)
) USING GiST (footprint);

-- Vehicles (dynamic, TTL)
CREATE TABLE vehicles (
    id UUID PRIMARY KEY,
    city_id UUID REFERENCES cities,
    type VARCHAR(50),
    position GEOMETRY(Point),
    velocity_x FLOAT,
    velocity_y FLOAT,
    spawned_at TIMESTAMP,
    expires_at TIMESTAMP,
    INDEX vehicle_city (city_id),
    INDEX vehicle_expires (expires_at)
);

-- Pedestrians (dynamic)
CREATE TABLE pedestrians (
    id UUID PRIMARY KEY,
    city_id UUID REFERENCES cities,
    position GEOMETRY(Point),
    destination GEOMETRY(Point),
    group_id UUID,
    speed FLOAT,
    spawned_at TIMESTAMP,
    expires_at TIMESTAMP,
    INDEX ped_city (city_id)
);

-- World Snapshots (for replay)
CREATE TABLE world_snapshots (
    id UUID PRIMARY KEY,
    city_id UUID REFERENCES cities,
    timestamp TIMESTAMP,
    vehicle_state JSONB,
    pedestrian_state JSONB,
    weather_state JSONB,
    season INT,
    INDEX snapshot_city_time (city_id, timestamp)
);

-- Create indexes
CREATE INDEX idx_buildings_city_geom ON buildings USING GiST (city_id, footprint);
CREATE INDEX idx_vehicles_position ON vehicles USING GiST (position);
CREATE INDEX idx_pedestrians_position ON pedestrians USING GiST (position);
```

### API Integration

```python
@app.post("/api/v1/cities/{city_id}/save")
async def save_city_snapshot(city_id: str) -> Dict:
    """Save current world state to database."""
    
    snapshot = {
        "city_id": city_id,
        "timestamp": datetime.now(),
        "vehicles": serialize_vehicles(),
        "pedestrians": serialize_pedestrians(),
        "weather": serialize_weather(),
    }
    
    db.save_snapshot(snapshot)
    return {"snapshot_id": snapshot["id"], "status": "saved"}

@app.get("/api/v1/cities/{city_id}/replay/{snapshot_id}")
async def load_snapshot(city_id: str, snapshot_id: str):
    """Load saved world state."""
    
    snapshot = db.load_snapshot(snapshot_id)
    world = reconstruct_world_from_snapshot(snapshot)
    
    return {"world_id": world.id, "status": "loaded"}
```

---

## Week 7-8: Integration & Testing

### Integration Tests

```python
# tests/integration/test_phase1_complete.py
class TestPhase1Complete:
    async def test_full_city_simulation(self):
        """End-to-end: Generate city, populate with traffic/pedestrians."""
        
        # 1. Generate city
        gen_response = await client.post("/api/v1/cities/generate", json={
            "seed": 42,
            "style": "downtown",
            "size_km": 2,
        })
        assert gen_response.status_code == 200
        city_id = gen_response.json()["city_id"]
        
        # 2. Load world
        city_spec = await fetch_city_spec(city_id)
        
        # 3. Simulate traffic
        for i in range(100):
            spawn_response = await client.post("/api/v1/traffic/spawn", json={
                "city_id": city_id,
                "density": 0.5,
            })
            assert spawn_response.status_code == 200
        
        # 4. Simulate pedestrians
        for i in range(200):
            spawn_response = await client.post("/api/v1/pedestrians/spawn", json={
                "city_id": city_id,
            })
            assert spawn_response.status_code == 200
        
        # 5. Update weather
        weather_response = await client.post("/api/v1/weather/update", json={
            "city_id": city_id,
            "rain_intensity": 0.3,
            "time_of_day": 14,
        })
        assert weather_response.status_code == 200
        
        # 6. Simulate for 100 seconds
        for step in range(10000):
            sim_response = await client.post("/api/v1/simulation/step", json={
                "city_id": city_id,
                "dt": 0.01,
            })
            assert sim_response.status_code == 200
        
        # 7. Verify results
        stats = await client.get(f"/api/v1/cities/{city_id}/stats")
        assert stats.json()["vehicle_count"] < 100  # Some arrived
        assert stats.json()["pedestrian_count"] < 200
    
    async def test_streaming_performance(self):
        """Verify streaming doesn't cause frame drops."""
        
        city = create_test_city(2000, 2000)
        
        # Simulate camera moving across city (causes streaming)
        for x in range(0, 2000, 100):
            streaming_manager.update_viewport(x, 1000)
            
            # Check frame rate maintained
            fps = 1.0 / dt
            assert fps > 25  # At least 25 FPS
    
    async def test_database_persistence(self):
        """Verify city saves/loads correctly."""
        
        city_id = await generate_test_city()
        
        # Save snapshot
        await client.post(f"/api/v1/cities/{city_id}/save")
        
        # Simulate for a while
        for _ in range(1000):
            await client.post(f"/api/v1/simulation/step", json={"city_id": city_id})
        
        # Load snapshot
        loaded = await client.get(f"/api/v1/cities/{city_id}/snapshots/latest")
        
        # Verify state matches
        assert loaded.json()["building_count"] > 0
```

### Performance Benchmarks

```python
# benchmarks/phase1_performance.py
class Phase1Benchmarks:
    def benchmark_city_generation(self):
        """Time city generation."""
        import time
        
        start = time.time()
        generator = CityGenerator(seed=42, style=CityStyle.DOWNTOWN)
        city = generator.generate(2000, 2000)
        elapsed = time.time() - start
        
        print(f"Generated 2km × 2km city in {elapsed:.1f}s")
        print(f"  Buildings: {len(city.buildings)}")
        print(f"  Roads: {len(city.roads)}")
        print(f"  Trees: {len(city.vegetation)}")
        
        assert elapsed < 30  # Should complete in <30s
    
    def benchmark_traffic_simulation(self):
        """Time traffic simulation with 1000 vehicles."""
        import time
        
        city = create_test_city()
        simulator = TrafficSimulator(city)
        
        # Spawn 1000 vehicles
        for _ in range(1000):
            simulator.spawn_vehicle((0, 0), (2000, 2000))
        
        start = time.time()
        for _ in range(1000):  # 10 seconds simulated
            simulator.update(0.01)
        elapsed = time.time() - start
        
        print(f"Simulated 1000 vehicles for 10s in {elapsed:.1f}s")
        print(f"  Real-time ratio: {10.0 / elapsed:.2f}x")
        
        assert elapsed < 20  # 10s simulation in <20s wall clock
    
    def benchmark_streaming(self):
        """Time chunk loading."""
        import time
        
        city = create_large_city(2000, 2000)
        manager = StreamingManager(city)
        
        start = time.time()
        for x in range(0, 2000, 100):
            manager.update_viewport(x, 1000)
        elapsed = time.time() - start
        
        print(f"Streamed {20} chunk transitions in {elapsed:.3f}s")
        assert elapsed < 5  # Should be fast
```

---

## Summary: Phase 1 Week-by-Week

| Week | Component | Tasks | Tests |
|------|-----------|-------|-------|
| 1-2 | Procedural Generation | L-System roads, Voronoi lots, building generation | 5 unit tests |
| 3-4 | Traffic | Pathfinding, physics, collision avoidance | 3 integration tests |
| 4-5 | Pedestrians | Social forces, grouping, destination selection | 2 integration tests |
| 5 | Weather & Seasons | Dynamic weather, seasonal colors | 2 unit tests |
| 6-7 | Streaming & Persistence | Chunking, PostgreSQL, snapshots | 3 integration tests |
| 7-8 | Integration & Testing | End-to-end tests, performance benchmarks | 5 integration tests |

**Total:** ~20 unit tests + 20 integration tests + 5 performance benchmarks

---

## Deliverables: v0.2.0

### Code
- `city_generator.py` (~800 lines)
- `traffic_system.py` (~700 lines)
- `pedestrian_system.py` (~600 lines)
- `weather_system.py` (~300 lines)
- `streaming.py` (~400 lines)
- Tests: 50+ test cases

### Data
- PostgreSQL schema (cities, buildings, vehicles, pedestrians, snapshots)
- 50,000+ buildings per city
- 1,000+ simultaneous vehicles
- 500+ pedestrians

### APIs
- `POST /api/v1/cities/generate`
- `POST /api/v1/traffic/spawn`
- `POST /api/v1/pedestrians/spawn`
- `POST /api/v1/weather/update`
- `POST /api/v1/cities/{id}/save`
- `GET /api/v1/cities/{id}/stats`

---

**Phase 1 Implementation Guide Complete**  
**Ready for 8-week execution**
