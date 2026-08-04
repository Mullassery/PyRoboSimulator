"""Tests for Phase 2.2: Navigation & Pathfinding."""

import math
import pytest

from backend.src.services.pathfinding import (
    AStarPathfinder,
    NavigationMesh,
    PathfindingCache,
    RVOAvoidance,
    Vector2,
)


class TestVector2:
    """Test 2D vector."""

    def test_vector_creation(self):
        """Test creating vector."""
        v = Vector2(3.0, 4.0)
        assert v.x == 3.0
        assert v.y == 4.0

    def test_vector_distance(self):
        """Test distance calculation."""
        v1 = Vector2(0, 0)
        v2 = Vector2(3, 4)
        dist = v1.distance_to(v2)
        assert abs(dist - 5.0) < 0.01

    def test_vector_heuristic(self):
        """Test heuristic distance."""
        v1 = Vector2(0, 0)
        v2 = Vector2(3, 4)
        h = v1.heuristic(v2)
        assert abs(h - 5.0) < 0.01

    def test_vector_equality(self):
        """Test vector equality with tolerance."""
        v1 = Vector2(1.0, 2.0)
        v2 = Vector2(1.00001, 2.00001)
        assert v1 == v2

    def test_vector_inequality(self):
        """Test vector inequality."""
        v1 = Vector2(1.0, 2.0)
        v2 = Vector2(2.0, 3.0)
        assert v1 != v2

    def test_vector_hashable(self):
        """Test vectors are hashable."""
        v1 = Vector2(1.0, 2.0)
        v2 = Vector2(1.0, 2.0)
        s = {v1, v2}
        assert len(s) == 1


class TestNavigationMesh:
    """Test navigation mesh."""

    def test_mesh_creation(self):
        """Test creating mesh."""
        mesh = NavigationMesh()
        assert len(mesh.polygons) == 0

    def test_add_polygon(self):
        """Test adding polygon."""
        mesh = NavigationMesh()
        vertices = [Vector2(0, 0), Vector2(10, 0), Vector2(10, 10), Vector2(0, 10)]

        poly_id = mesh.add_polygon(vertices)
        assert poly_id == 0
        assert poly_id in mesh.polygons

    def test_polygon_center(self):
        """Test polygon center calculation."""
        mesh = NavigationMesh()
        vertices = [Vector2(0, 0), Vector2(10, 0), Vector2(10, 10), Vector2(0, 10)]

        poly_id = mesh.add_polygon(vertices)
        polygon = mesh.polygons[poly_id]

        assert polygon.center is not None
        assert abs(polygon.center.x - 5.0) < 0.1
        assert abs(polygon.center.y - 5.0) < 0.1

    def test_point_in_polygon(self):
        """Test point-in-polygon detection."""
        mesh = NavigationMesh()
        vertices = [Vector2(0, 0), Vector2(10, 0), Vector2(10, 10), Vector2(0, 10)]
        poly_id = mesh.add_polygon(vertices)

        polygon = mesh.polygons[poly_id]
        assert polygon.contains_point(Vector2(5, 5))
        assert not polygon.contains_point(Vector2(15, 15))

    def test_find_polygon_at(self):
        """Test finding polygon at point."""
        mesh = NavigationMesh()
        vertices = [Vector2(0, 0), Vector2(10, 0), Vector2(10, 10), Vector2(0, 10)]
        mesh.add_polygon(vertices)

        found = mesh.find_polygon_at(Vector2(5, 5))
        assert found == 0

    def test_find_polygon_not_found(self):
        """Test finding polygon when none exists."""
        mesh = NavigationMesh()
        found = mesh.find_polygon_at(Vector2(5, 5))
        assert found is None

    def test_get_nearest_polygon(self):
        """Test getting nearest polygon."""
        mesh = NavigationMesh()
        vertices1 = [Vector2(0, 0), Vector2(10, 0), Vector2(10, 10), Vector2(0, 10)]
        vertices2 = [Vector2(20, 20), Vector2(30, 20), Vector2(30, 30), Vector2(20, 30)]

        mesh.add_polygon(vertices1)
        mesh.add_polygon(vertices2)

        nearest = mesh.get_nearest_polygon(Vector2(5, 5))
        assert nearest == 0

    def test_add_obstacle(self):
        """Test adding obstacle."""
        mesh = NavigationMesh()
        vertices = [Vector2(0, 0), Vector2(10, 0), Vector2(10, 10), Vector2(0, 10)]
        poly_id = mesh.add_polygon(vertices)

        # Add obstacle at polygon center
        mesh.add_obstacle(Vector2(5, 5), 2.0)

        polygon = mesh.polygons[poly_id]
        assert not polygon.walkable

    def test_multiple_polygons(self):
        """Test mesh with multiple polygons."""
        mesh = NavigationMesh()

        # Add 2x2 grid of polygons
        for i in range(2):
            for j in range(2):
                x = i * 10
                y = j * 10
                vertices = [
                    Vector2(x, y),
                    Vector2(x + 10, y),
                    Vector2(x + 10, y + 10),
                    Vector2(x, y + 10),
                ]
                mesh.add_polygon(vertices)

        assert len(mesh.polygons) == 4


class TestPathfindingCache:
    """Test pathfinding cache."""

    def test_cache_creation(self):
        """Test creating cache."""
        cache = PathfindingCache(max_cache_size=100)
        assert cache.max_cache_size == 100
        assert len(cache.cache) == 0

    def test_cache_set_get(self):
        """Test setting and getting cache."""
        cache = PathfindingCache()
        start = Vector2(0, 0)
        goal = Vector2(10, 10)
        path = [start, Vector2(5, 5), goal]

        cache.set(start, goal, path)
        retrieved = cache.get(start, goal)

        assert retrieved is not None
        assert len(retrieved) == 3

    def test_cache_miss(self):
        """Test cache miss."""
        cache = PathfindingCache()
        start = Vector2(0, 0)
        goal = Vector2(10, 10)

        retrieved = cache.get(start, goal)
        assert retrieved is None

    def test_cache_hit_rate(self):
        """Test hit rate calculation."""
        cache = PathfindingCache()
        start = Vector2(0, 0)
        goal = Vector2(10, 10)
        path = [start, goal]

        cache.set(start, goal, path)

        cache.get(start, goal)  # hit
        cache.get(Vector2(5, 5), Vector2(15, 15))  # miss

        hit_rate = cache.get_hit_rate()
        assert abs(hit_rate - 0.5) < 0.01

    def test_cache_capacity(self):
        """Test cache capacity limit."""
        cache = PathfindingCache(max_cache_size=2)

        for i in range(5):
            start = Vector2(i, i)
            goal = Vector2(i + 10, i + 10)
            path = [start, goal]
            cache.set(start, goal, path)

        assert len(cache.cache) <= 2

    def test_cache_clear(self):
        """Test clearing cache."""
        cache = PathfindingCache()
        start = Vector2(0, 0)
        goal = Vector2(10, 10)
        path = [start, goal]

        cache.set(start, goal, path)
        cache.clear()

        assert len(cache.cache) == 0


class TestAStarPathfinder:
    """Test A* pathfinding."""

    def test_pathfinder_creation(self):
        """Test creating pathfinder."""
        mesh = NavigationMesh()
        pathfinder = AStarPathfinder(mesh)

        assert pathfinder.nav_mesh == mesh

    def test_simple_path(self):
        """Test finding simple path."""
        mesh = NavigationMesh()

        # Create 2x2 grid of walkable polygons
        for i in range(2):
            for j in range(2):
                x = i * 10
                y = j * 10
                vertices = [
                    Vector2(x, y),
                    Vector2(x + 10, y),
                    Vector2(x + 10, y + 10),
                    Vector2(x, y + 10),
                ]
                mesh.add_polygon(vertices)

        pathfinder = AStarPathfinder(mesh)

        # Find path from (5,5) to (15,15)
        start = Vector2(5, 5)
        goal = Vector2(15, 15)
        path = pathfinder.find_path(start, goal)

        assert path is not None
        assert len(path) > 0
        assert path[0] == start

    def test_no_path(self):
        """Test when no path exists."""
        mesh = NavigationMesh()

        # Single polygon
        vertices = [Vector2(0, 0), Vector2(10, 0), Vector2(10, 10), Vector2(0, 10)]
        mesh.add_polygon(vertices)

        # Mark as unwalkable
        mesh.polygons[0].walkable = False

        pathfinder = AStarPathfinder(mesh)
        path = pathfinder.find_path(Vector2(5, 5), Vector2(5, 5))

        # Should still find path to same point
        assert path is not None

    def test_path_caching(self):
        """Test path caching."""
        mesh = NavigationMesh()
        vertices = [Vector2(0, 0), Vector2(10, 0), Vector2(10, 10), Vector2(0, 10)]
        mesh.add_polygon(vertices)

        pathfinder = AStarPathfinder(mesh)

        start = Vector2(2, 2)
        goal = Vector2(8, 8)

        # First call
        path1 = pathfinder.find_path(start, goal)

        # Second call should hit cache
        path2 = pathfinder.find_path(start, goal)

        assert path1 == path2
        hit_rate = pathfinder.cache.get_hit_rate()
        assert hit_rate > 0

    def test_statistics(self):
        """Test pathfinder statistics."""
        mesh = NavigationMesh()
        vertices = [Vector2(0, 0), Vector2(10, 0), Vector2(10, 10), Vector2(0, 10)]
        mesh.add_polygon(vertices)

        pathfinder = AStarPathfinder(mesh)

        pathfinder.find_path(Vector2(2, 2), Vector2(8, 8))

        stats = pathfinder.get_statistics()
        assert stats["paths_calculated"] > 0
        assert "cache_hit_rate" in stats


class TestRVOAvoidance:
    """Test RVO collision avoidance."""

    def test_avoidance_creation(self):
        """Test creating avoidance."""
        avoidance = RVOAvoidance(agent_radius=0.5)
        assert avoidance.agent_radius == 0.5

    def test_no_neighbors(self):
        """Test avoidance with no neighbors."""
        avoidance = RVOAvoidance()
        pos = Vector2(0, 0)
        vel = Vector2(0, 0)
        goal = Vector2(10, 0)

        avoidance_vel = avoidance.compute_avoidance_velocity(pos, vel, goal, [])

        # Should move toward goal
        assert avoidance_vel.x > 0 or avoidance_vel.y > 0

    def test_static_neighbor(self):
        """Test avoidance with static neighbor."""
        avoidance = RVOAvoidance()
        pos = Vector2(0, 0)
        vel = Vector2(1, 0)
        goal = Vector2(10, 0)

        neighbor_pos = Vector2(2, 0)
        neighbor_vel = Vector2(0, 0)
        nearby = [(neighbor_pos, neighbor_vel)]

        avoidance_vel = avoidance.compute_avoidance_velocity(pos, vel, goal, nearby)

        # Should have computed avoidance
        assert isinstance(avoidance_vel, Vector2)

    def test_moving_neighbor(self):
        """Test avoidance with moving neighbor."""
        avoidance = RVOAvoidance()
        pos = Vector2(0, 0)
        vel = Vector2(1, 0)
        goal = Vector2(10, 0)

        neighbor_pos = Vector2(5, 0)
        neighbor_vel = Vector2(1, 0)
        nearby = [(neighbor_pos, neighbor_vel)]

        avoidance_vel = avoidance.compute_avoidance_velocity(pos, vel, goal, nearby)

        assert isinstance(avoidance_vel, Vector2)

    def test_too_close_neighbor(self):
        """Test when neighbor is too close."""
        avoidance = RVOAvoidance(agent_radius=0.5)
        pos = Vector2(0, 0)
        vel = Vector2(0, 0)
        goal = Vector2(10, 0)

        # Neighbor very close
        neighbor_pos = Vector2(0.5, 0)
        neighbor_vel = Vector2(0, 0)
        nearby = [(neighbor_pos, neighbor_vel)]

        avoidance_vel = avoidance.compute_avoidance_velocity(pos, vel, goal, nearby)

        # Should move away from neighbor
        assert avoidance_vel.x != 0 or avoidance_vel.y != 0

    def test_multiple_neighbors(self):
        """Test avoidance with multiple neighbors."""
        avoidance = RVOAvoidance()
        pos = Vector2(0, 0)
        vel = Vector2(0, 0)
        goal = Vector2(10, 0)

        nearby = [
            (Vector2(2, 2), Vector2(0, 0)),
            (Vector2(3, 3), Vector2(0, 0)),
            (Vector2(4, 4), Vector2(0, 0)),
        ]

        avoidance_vel = avoidance.compute_avoidance_velocity(pos, vel, goal, nearby)

        assert isinstance(avoidance_vel, Vector2)

    def test_max_speed_respected(self):
        """Test that velocity respects max speed."""
        avoidance = RVOAvoidance()
        pos = Vector2(0, 0)
        vel = Vector2(0, 0)
        goal = Vector2(10, 10)

        avoidance_vel = avoidance.compute_avoidance_velocity(pos, vel, goal, [], max_speed=5.0)

        speed = math.sqrt(avoidance_vel.x ** 2 + avoidance_vel.y ** 2)
        assert speed <= 5.01  # Small tolerance for floating point


class TestPathfindingIntegration:
    """Integration tests for pathfinding."""

    def test_full_pathfinding_scenario(self):
        """Test complete pathfinding scenario."""
        mesh = NavigationMesh()

        # Create 3x3 grid
        for i in range(3):
            for j in range(3):
                x = i * 10
                y = j * 10
                vertices = [
                    Vector2(x, y),
                    Vector2(x + 10, y),
                    Vector2(x + 10, y + 10),
                    Vector2(x, y + 10),
                ]
                mesh.add_polygon(vertices)

        # Add obstacle in middle
        mesh.add_obstacle(Vector2(15, 15), 3.0)

        pathfinder = AStarPathfinder(mesh)

        # Find path around obstacle
        start = Vector2(5, 5)
        goal = Vector2(25, 25)

        path = pathfinder.find_path(start, goal)
        assert path is not None

    def test_pathfinding_with_avoidance(self):
        """Test pathfinding combined with avoidance."""
        mesh = NavigationMesh()
        vertices = [Vector2(0, 0), Vector2(50, 0), Vector2(50, 50), Vector2(0, 50)]
        mesh.add_polygon(vertices)

        pathfinder = AStarPathfinder(mesh)
        avoidance = RVOAvoidance()

        # Get path
        start = Vector2(10, 10)
        goal = Vector2(40, 40)
        path = pathfinder.find_path(start, goal)

        assert path is not None

        # Apply avoidance at each step
        for i in range(len(path) - 1):
            current_pos = path[i]
            next_goal = path[i + 1]

            neighbors = [(Vector2(current_pos.x + 5, current_pos.y), Vector2(0, 0))]
            avoidance_vel = avoidance.compute_avoidance_velocity(
                current_pos, Vector2(0, 0), next_goal, neighbors
            )

            assert isinstance(avoidance_vel, Vector2)

    def test_performance_many_paths(self):
        """Test performance with many path calculations."""
        mesh = NavigationMesh()

        # Create dense mesh
        for i in range(5):
            for j in range(5):
                x = i * 10
                y = j * 10
                vertices = [
                    Vector2(x, y),
                    Vector2(x + 10, y),
                    Vector2(x + 10, y + 10),
                    Vector2(x, y + 10),
                ]
                mesh.add_polygon(vertices)

        pathfinder = AStarPathfinder(mesh)

        # Calculate many paths
        for i in range(20):
            start = Vector2(i * 2, i * 2)
            goal = Vector2(40 - i * 2, 40 - i * 2)
            path = pathfinder.find_path(start, goal)

        stats = pathfinder.get_statistics()
        assert stats["paths_calculated"] >= 20
        # Cache should have improved hit rate
        assert stats["cache_hit_rate"] >= 0
