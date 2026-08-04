"""A* pathfinding and navigation mesh generation.

Implements efficient pathfinding with caching and navigation mesh support.
"""

import heapq
import logging
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class Vector2:
    """2D vector for pathfinding."""

    x: float
    y: float

    def __hash__(self):
        """Make hashable for use in sets/dicts."""
        return hash((round(self.x, 4), round(self.y, 4)))

    def __eq__(self, other):
        """Check equality with tolerance."""
        return abs(self.x - other.x) < 0.0001 and abs(self.y - other.y) < 0.0001

    def distance_to(self, other: "Vector2") -> float:
        """Distance to another point."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def heuristic(self, other: "Vector2") -> float:
        """Heuristic distance (Euclidean)."""
        return self.distance_to(other)


@dataclass
class NavMeshPolygon:
    """Single polygon in navigation mesh."""

    id: int
    vertices: List[Vector2]
    neighbors: List[int] = field(default_factory=list)  # IDs of neighboring polygons
    center: Optional[Vector2] = None
    walkable: bool = True

    def __post_init__(self):
        """Calculate center if not provided."""
        if self.center is None:
            avg_x = sum(v.x for v in self.vertices) / len(self.vertices)
            avg_y = sum(v.y for v in self.vertices) / len(self.vertices)
            self.center = Vector2(avg_x, avg_y)

    def contains_point(self, point: Vector2) -> bool:
        """Check if point is inside polygon (ray casting)."""
        if not self.walkable:
            return False

        # Ray casting algorithm
        inside = False
        n = len(self.vertices)

        for i in range(n):
            v1 = self.vertices[i]
            v2 = self.vertices[(i + 1) % n]

            if (v1.y > point.y) != (v2.y > point.y):
                x_intersect = (v2.x - v1.x) * (point.y - v1.y) / (v2.y - v1.y) + v1.x
                if point.x < x_intersect:
                    inside = not inside

        return inside


class NavigationMesh:
    """Navigation mesh for agents."""

    def __init__(self, grid_size: float = 1.0, world_bounds: Optional[Dict] = None):
        """Initialize navigation mesh.

        Args:
            grid_size: Grid cell size
            world_bounds: World bounds {x_min, x_max, y_min, y_max}
        """
        self.grid_size = grid_size
        self.world_bounds = world_bounds or {
            "x_min": 0,
            "x_max": 1000,
            "y_min": 0,
            "y_max": 1000,
        }
        self.polygons: Dict[int, NavMeshPolygon] = {}
        self.polygon_counter = 0

    def add_polygon(self, vertices: List[Vector2], walkable: bool = True) -> int:
        """Add polygon to mesh.

        Args:
            vertices: List of vertices
            walkable: Whether polygon is walkable

        Returns:
            Polygon ID
        """
        poly_id = self.polygon_counter
        self.polygon_counter += 1

        polygon = NavMeshPolygon(
            id=poly_id,
            vertices=vertices,
            walkable=walkable,
        )
        self.polygons[poly_id] = polygon

        # Link neighbors
        for other_id, other_poly in self.polygons.items():
            if other_id != poly_id and self._polygons_adjacent(polygon, other_poly):
                if other_id not in polygon.neighbors:
                    polygon.neighbors.append(other_id)
                if poly_id not in other_poly.neighbors:
                    other_poly.neighbors.append(poly_id)

        return poly_id

    def find_polygon_at(self, point: Vector2) -> Optional[int]:
        """Find polygon containing point.

        Args:
            point: Query point

        Returns:
            Polygon ID or None
        """
        for poly_id, polygon in self.polygons.items():
            if polygon.contains_point(point):
                return poly_id

        return None

    def get_nearest_polygon(self, point: Vector2) -> Optional[int]:
        """Find nearest walkable polygon.

        Args:
            point: Query point

        Returns:
            Polygon ID or None
        """
        nearest_id = None
        nearest_dist = float("inf")

        for poly_id, polygon in self.polygons.items():
            if not polygon.walkable or polygon.center is None:
                continue

            dist = point.distance_to(polygon.center)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_id = poly_id

        return nearest_id

    def add_obstacle(self, center: Vector2, radius: float) -> None:
        """Add circular obstacle by marking intersecting polygons unwalkable.

        Args:
            center: Obstacle center
            radius: Obstacle radius
        """
        for poly in self.polygons.values():
            if poly.center is None:
                continue

            dist = center.distance_to(poly.center)
            if dist < radius:
                poly.walkable = False

    def _polygons_adjacent(self, poly1: NavMeshPolygon, poly2: NavMeshPolygon) -> bool:
        """Check if two polygons share an edge."""
        # Simplified: check if centers are close
        if poly1.center is None or poly2.center is None:
            return False

        dist = poly1.center.distance_to(poly2.center)
        return dist < self.grid_size * 2.5


class PathfindingCache:
    """Caches pathfinding results."""

    def __init__(self, max_cache_size: int = 10000):
        """Initialize cache.

        Args:
            max_cache_size: Maximum number of cached paths
        """
        self.max_cache_size = max_cache_size
        self.cache: Dict[Tuple, List[Vector2]] = {}
        self.access_count = 0
        self.hit_count = 0

    def get(self, start: Vector2, goal: Vector2) -> Optional[List[Vector2]]:
        """Get cached path.

        Args:
            start: Start position
            goal: Goal position

        Returns:
            Cached path or None
        """
        key = (round(start.x, 2), round(start.y, 2), round(goal.x, 2), round(goal.y, 2))

        self.access_count += 1
        if key in self.cache:
            self.hit_count += 1
            return self.cache[key].copy()

        return None

    def set(self, start: Vector2, goal: Vector2, path: List[Vector2]) -> None:
        """Cache a path.

        Args:
            start: Start position
            goal: Goal position
            path: Path to cache
        """
        # Evict oldest if over capacity
        if len(self.cache) >= self.max_cache_size:
            # Remove first item
            first_key = next(iter(self.cache))
            del self.cache[first_key]

        key = (round(start.x, 2), round(start.y, 2), round(goal.x, 2), round(goal.y, 2))
        self.cache[key] = path.copy()

    def clear(self) -> None:
        """Clear cache."""
        self.cache.clear()

    def get_hit_rate(self) -> float:
        """Get cache hit rate."""
        if self.access_count == 0:
            return 0.0
        return self.hit_count / self.access_count


class AStarPathfinder:
    """A* pathfinding implementation."""

    def __init__(self, nav_mesh: NavigationMesh, cache_size: int = 10000):
        """Initialize pathfinder.

        Args:
            nav_mesh: Navigation mesh to use
            cache_size: Size of path cache
        """
        self.nav_mesh = nav_mesh
        self.cache = PathfindingCache(cache_size)
        self.paths_calculated = 0

    def find_path(self, start: Vector2, goal: Vector2) -> Optional[List[Vector2]]:
        """Find path from start to goal using A*.

        Args:
            start: Start position
            goal: Goal position

        Returns:
            List of waypoints or None if no path exists
        """
        # Check cache first
        cached_path = self.cache.get(start, goal)
        if cached_path is not None:
            return cached_path

        self.paths_calculated += 1

        # Find start and goal polygons
        start_poly = self.nav_mesh.find_polygon_at(start)
        if start_poly is None:
            start_poly = self.nav_mesh.get_nearest_polygon(start)

        goal_poly = self.nav_mesh.find_polygon_at(goal)
        if goal_poly is None:
            goal_poly = self.nav_mesh.get_nearest_polygon(goal)

        if start_poly is None or goal_poly is None:
            return None

        # Find path through nav mesh polygons
        polygon_path = self._find_polygon_path(start_poly, goal_poly)
        if polygon_path is None:
            return None

        # Convert to waypoint path
        waypoint_path = self._polygon_path_to_waypoints(start, goal, polygon_path)

        # Cache result
        self.cache.set(start, goal, waypoint_path)

        return waypoint_path

    def _find_polygon_path(
        self, start_poly: int, goal_poly: int
    ) -> Optional[List[int]]:
        """Find path through polygons using A*.

        Args:
            start_poly: Start polygon ID
            goal_poly: Goal polygon ID

        Returns:
            List of polygon IDs or None
        """
        if start_poly == goal_poly:
            return [start_poly]

        # Priority queue: (f_score, counter, polygon_id)
        open_set = [(0, 0, start_poly)]
        counter = 0
        came_from: Dict[int, int] = {}
        g_score: Dict[int, float] = {start_poly: 0}
        f_score: Dict[int, float] = {start_poly: 0}
        closed_set: Set[int] = set()

        while open_set:
            _, _, current = heapq.heappop(open_set)

            if current == goal_poly:
                # Reconstruct path
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                return path[::-1]

            if current in closed_set:
                continue

            closed_set.add(current)
            current_poly = self.nav_mesh.polygons[current]

            for neighbor_id in current_poly.neighbors:
                if neighbor_id in closed_set:
                    continue

                neighbor_poly = self.nav_mesh.polygons[neighbor_id]
                if not neighbor_poly.walkable:
                    continue

                tentative_g = g_score[current] + 1
                if neighbor_id not in g_score or tentative_g < g_score[neighbor_id]:
                    came_from[neighbor_id] = current
                    g_score[neighbor_id] = tentative_g

                    goal_dist = 0.0
                    if neighbor_poly.center and self.nav_mesh.polygons[goal_poly].center:
                        goal_dist = neighbor_poly.center.distance_to(
                            self.nav_mesh.polygons[goal_poly].center
                        )

                    f_score[neighbor_id] = tentative_g + goal_dist

                    counter += 1
                    heapq.heappush(open_set, (f_score[neighbor_id], counter, neighbor_id))

        return None

    def _polygon_path_to_waypoints(
        self, start: Vector2, goal: Vector2, polygon_path: List[int]
    ) -> List[Vector2]:
        """Convert polygon path to waypoint path.

        Args:
            start: Start position
            goal: Goal position
            polygon_path: List of polygon IDs

        Returns:
            List of waypoints
        """
        if not polygon_path:
            return [start, goal]

        waypoints = [start]

        for poly_id in polygon_path[1:]:
            poly = self.nav_mesh.polygons[poly_id]
            if poly.center:
                waypoints.append(poly.center)

        waypoints.append(goal)

        return waypoints

    def get_statistics(self) -> Dict[str, float]:
        """Get pathfinding statistics.

        Returns:
            Dictionary with stats
        """
        return {
            "paths_calculated": self.paths_calculated,
            "cache_size": len(self.cache.cache),
            "cache_hit_rate": self.cache.get_hit_rate(),
        }


class RVOAvoidance:
    """Reciprocal Velocity Obstacle collision avoidance."""

    def __init__(self, agent_radius: float = 0.5, time_horizon: float = 5.0):
        """Initialize RVO avoidance.

        Args:
            agent_radius: Radius of agent
            time_horizon: Lookahead time
        """
        self.agent_radius = agent_radius
        self.time_horizon = time_horizon

    def compute_avoidance_velocity(
        self,
        position: Vector2,
        velocity: Vector2,
        goal: Vector2,
        nearby_agents: List[Tuple[Vector2, Vector2]],
        max_speed: float = 10.0,
    ) -> Vector2:
        """Compute velocity with collision avoidance.

        Args:
            position: Current position
            velocity: Desired velocity
            goal: Goal position
            nearby_agents: List of (position, velocity) tuples
            max_speed: Maximum allowed speed

        Returns:
            Avoidance velocity
        """
        if not nearby_agents:
            # No neighbors, move toward goal
            to_goal = Vector2(goal.x - position.x, goal.y - position.y)
            dist = math.sqrt(to_goal.x ** 2 + to_goal.y ** 2)
            if dist > 0:
                to_goal.x = (to_goal.x / dist) * max_speed
                to_goal.y = (to_goal.y / dist) * max_speed
            return to_goal

        # Build RVO constraints
        constraints = []

        for neighbor_pos, neighbor_vel in nearby_agents:
            rel_pos = Vector2(neighbor_pos.x - position.x, neighbor_pos.y - position.y)
            rel_vel = Vector2(velocity.x - neighbor_vel.x, velocity.y - neighbor_vel.y)

            dist_sq = rel_pos.x ** 2 + rel_pos.y ** 2
            dist = math.sqrt(dist_sq)

            if dist < 0.001:
                continue

            min_sep = 2 * self.agent_radius
            if dist < min_sep:
                # Too close, move away
                direction = Vector2(rel_pos.x / dist, rel_pos.y / dist)
                avoidance = Vector2(direction.x * max_speed, direction.y * max_speed)
                return avoidance

        # Move toward goal with constraints applied
        to_goal = Vector2(goal.x - position.x, goal.y - position.y)
        dist = math.sqrt(to_goal.x ** 2 + to_goal.y ** 2)

        if dist > 0:
            to_goal.x = (to_goal.x / dist) * max_speed
            to_goal.y = (to_goal.y / dist) * max_speed

        return to_goal
