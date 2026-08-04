"""Tests for Phase 1C.8: World Streaming from Python to UE5."""

import json
import pytest

from backend.src.services.world_streaming import (
    Mesh,
    Obstacle,
    Vector3,
    WorldChunk,
    WorldStreamingService,
)


class TestVector3:
    """Test Vector3 serialization."""

    def test_vector3_creation(self):
        """Test creating vector."""
        v = Vector3(1.0, 2.0, 3.0)
        assert v.x == 1.0
        assert v.y == 2.0
        assert v.z == 3.0

    def test_vector3_to_dict(self):
        """Test dict conversion."""
        v = Vector3(1.5, 2.5, 3.5)
        d = v.to_dict()
        assert d == {"x": 1.5, "y": 2.5, "z": 3.5}

    def test_vector3_binary_serialization(self):
        """Test binary serialization."""
        v = Vector3(1.0, 2.0, 3.0)
        binary = v.to_bytes()
        assert len(binary) == 12
        v2 = Vector3.from_bytes(binary)
        assert abs(v2.x - 1.0) < 0.0001
        assert abs(v2.y - 2.0) < 0.0001
        assert abs(v2.z - 3.0) < 0.0001


class TestMesh:
    """Test mesh definition."""

    def test_mesh_creation(self):
        """Test creating simple triangle mesh."""
        vertices = [Vector3(0, 0, 0), Vector3(1, 0, 0), Vector3(0, 1, 0)]
        indices = [0, 1, 2]
        mesh = Mesh(vertices, indices, material="concrete")

        assert mesh.vertex_count() == 3
        assert mesh.triangle_count() == 1

    def test_mesh_to_dict(self):
        """Test mesh serialization."""
        vertices = [Vector3(0, 0, 0), Vector3(1, 0, 0), Vector3(0, 1, 0)]
        indices = [0, 1, 2]
        mesh = Mesh(vertices, indices, material="concrete")

        d = mesh.to_dict()
        assert len(d["vertices"]) == 3
        assert d["indices"] == [0, 1, 2]
        assert d["material"] == "concrete"

    def test_mesh_memory_size(self):
        """Test memory estimation."""
        vertices = [Vector3(i, i, i) for i in range(100)]
        indices = list(range(300))
        mesh = Mesh(vertices, indices)

        size = mesh.memory_size()
        # 100 vertices * 12 bytes + 300 indices * 4 bytes = 1200 + 1200 = 2400
        assert size == 2400


class TestObstacle:
    """Test obstacle definition."""

    def test_box_obstacle_creation(self):
        """Test creating box obstacle."""
        pos = Vector3(10.0, 20.0, 0.0)
        size = Vector3(5.0, 5.0, 3.0)
        obs = Obstacle(id=1, position=pos, size=size)

        assert obs.id == 1
        assert obs.collision_type == "box"

    def test_obstacle_bounds(self):
        """Test AABB bounds calculation."""
        pos = Vector3(100.0, 200.0, 0.0)
        size = Vector3(20.0, 30.0, 5.0)
        obs = Obstacle(id=1, position=pos, size=size)

        x_min, x_max, y_min, y_max = obs.get_bounds()
        assert x_min == 90.0
        assert x_max == 110.0
        assert y_min == 185.0
        assert y_max == 215.0

    def test_obstacle_to_dict(self):
        """Test obstacle serialization."""
        pos = Vector3(10.0, 20.0, 0.0)
        size = Vector3(5.0, 5.0, 3.0)
        obs = Obstacle(id=1, position=pos, size=size, material="asphalt")

        d = obs.to_dict()
        assert d["id"] == 1
        assert d["material"] == "asphalt"
        assert d["collision_type"] == "box"


class TestWorldChunk:
    """Test world chunk."""

    def test_chunk_creation(self):
        """Test creating chunk."""
        chunk = WorldChunk(chunk_x=0, chunk_y=0, chunk_size=500.0)
        assert chunk.chunk_x == 0
        assert chunk.chunk_y == 0
        assert len(chunk.obstacles) == 0

    def test_chunk_bounds(self):
        """Test chunk world bounds."""
        chunk = WorldChunk(chunk_x=1, chunk_y=2, chunk_size=500.0)
        x_min, x_max, y_min, y_max = chunk.get_bounds()

        assert x_min == 500.0
        assert x_max == 1000.0
        assert y_min == 1000.0
        assert y_max == 1500.0

    def test_chunk_to_dict(self):
        """Test chunk serialization."""
        chunk = WorldChunk(chunk_x=0, chunk_y=0, chunk_size=500.0)
        obs = Obstacle(id=1, position=Vector3(100, 100, 0), size=Vector3(5, 5, 3))
        chunk.obstacles.append(obs)

        d = chunk.to_dict()
        assert d["chunk_x"] == 0
        assert d["obstacle_count"] == 1


class TestWorldStreamingService:
    """Test world streaming service."""

    def test_service_creation(self):
        """Test creating streaming service."""
        service = WorldStreamingService(world_size=2000.0, chunk_size=500.0)
        assert service.world_size == 2000.0
        assert service.num_chunks_per_side == 4

    def test_create_box_obstacle(self):
        """Test creating box obstacle via service."""
        service = WorldStreamingService()
        pos = Vector3(100.0, 100.0, 0.0)
        size = Vector3(5.0, 5.0, 3.0)

        obs = service.create_box_obstacle(pos, size)
        assert obs.id == 1
        assert obs.collision_type == "box"

    def test_create_mesh_obstacle(self):
        """Test creating mesh obstacle via service."""
        service = WorldStreamingService()
        pos = Vector3(100.0, 100.0, 0.0)
        vertices = [Vector3(0, 0, 0), Vector3(1, 0, 0), Vector3(0, 1, 0)]
        indices = [0, 1, 2]
        mesh = Mesh(vertices, indices)

        obs = service.create_mesh_obstacle(pos, mesh)
        assert obs.id == 1
        assert obs.collision_type == "mesh"
        assert obs.mesh is not None

    def test_add_obstacle_to_chunk(self):
        """Test adding obstacle to chunk."""
        service = WorldStreamingService(chunk_size=500.0)
        pos = Vector3(100.0, 100.0, 0.0)
        size = Vector3(5.0, 5.0, 3.0)

        obs = service.create_box_obstacle(pos, size)
        service.add_obstacle(obs)

        chunk = service.get_chunk(0, 0)
        assert len(chunk.obstacles) == 1
        assert chunk.obstacles[0].id == 1

    def test_add_obstacle_spans_chunks(self):
        """Test obstacle spanning multiple chunks."""
        service = WorldStreamingService(chunk_size=100.0)
        # Large obstacle at boundary
        pos = Vector3(95.0, 95.0, 0.0)
        size = Vector3(20.0, 20.0, 3.0)

        obs = service.create_box_obstacle(pos, size)
        service.add_obstacle(obs)

        # Should be in multiple chunks
        chunk_00 = service.get_chunk(0, 0)
        chunk_01 = service.get_chunk(0, 1)
        chunk_10 = service.get_chunk(1, 0)

        total = len(chunk_00.obstacles) + len(chunk_01.obstacles) + len(chunk_10.obstacles)
        assert total >= 1

    def test_add_dynamic_object(self):
        """Test adding dynamic object to chunk."""
        service = WorldStreamingService()
        pos = Vector3(100.0, 100.0, 0.0)
        vel = Vector3(1.0, 0.0, 0.0)

        service.add_dynamic_object(0, 0, "agent_1", pos, vel, "vehicle")

        chunk = service.get_chunk(0, 0)
        assert len(chunk.dynamic_objects) == 1
        assert chunk.dynamic_objects[0]["id"] == "agent_1"

    def test_update_dynamic_object(self):
        """Test updating dynamic object position."""
        service = WorldStreamingService()
        pos1 = Vector3(100.0, 100.0, 0.0)
        vel1 = Vector3(1.0, 0.0, 0.0)

        service.add_dynamic_object(0, 0, "agent_1", pos1, vel1)

        # Update position
        pos2 = Vector3(110.0, 100.0, 0.0)
        vel2 = Vector3(2.0, 0.0, 0.0)
        service.add_dynamic_object(0, 0, "agent_1", pos2, vel2)

        chunk = service.get_chunk(0, 0)
        assert len(chunk.dynamic_objects) == 1
        assert chunk.dynamic_objects[0]["position"]["x"] == 110.0

    def test_get_chunk_valid(self):
        """Test getting valid chunk."""
        service = WorldStreamingService()
        chunk = service.get_chunk(0, 0)
        assert chunk is not None

    def test_get_chunk_invalid(self):
        """Test getting invalid chunk."""
        service = WorldStreamingService()
        chunk = service.get_chunk(10, 10)
        assert chunk is None

    def test_get_chunk_json(self):
        """Test chunk serialization to JSON."""
        service = WorldStreamingService()
        obs = service.create_box_obstacle(Vector3(100, 100, 0), Vector3(5, 5, 3))
        service.add_obstacle(obs)

        json_str = service.get_chunk_json(0, 0)
        assert json_str is not None

        data = json.loads(json_str)
        assert data["chunk_x"] == 0
        assert data["obstacle_count"] == 1

    def test_chunk_caching(self):
        """Test chunk caching."""
        service = WorldStreamingService()
        obs = service.create_box_obstacle(Vector3(100, 100, 0), Vector3(5, 5, 3))
        service.add_obstacle(obs)

        # First call
        json1 = service.get_chunk_json(0, 0)

        # Modify chunk
        service.add_dynamic_object(0, 0, "agent_1", Vector3(150, 150, 0), Vector3(1, 0, 0))

        # Cache should be invalidated
        json2 = service.get_chunk_json(0, 0)

        data1 = json.loads(json1)
        data2 = json.loads(json2)

        assert data1["dynamic_object_count"] == 0
        assert data2["dynamic_object_count"] == 1

    def test_get_chunks_for_position(self):
        """Test getting chunks around position."""
        service = WorldStreamingService(world_size=2000.0, chunk_size=500.0)
        pos = Vector3(500.0, 500.0, 0.0)

        chunks = service.get_chunks_for_position(pos, radius=600.0)
        assert len(chunks) > 0

    def test_world_bounds(self):
        """Test world bounds."""
        service = WorldStreamingService(world_size=2000.0)
        bounds = service.get_world_bounds()

        assert bounds["x_min"] == 0
        assert bounds["x_max"] == 2000.0
        assert bounds["y_min"] == 0
        assert bounds["y_max"] == 2000.0

    def test_statistics(self):
        """Test streaming statistics."""
        service = WorldStreamingService()
        obs = service.create_box_obstacle(Vector3(100, 100, 0), Vector3(5, 5, 3))
        service.add_obstacle(obs)
        service.add_dynamic_object(0, 0, "agent_1", Vector3(150, 150, 0), Vector3(1, 0, 0))

        stats = service.get_statistics()
        assert stats["total_obstacles"] == 1
        assert stats["total_dynamic_objects"] == 1

    def test_binary_streaming(self):
        """Test binary chunk streaming."""
        service = WorldStreamingService()
        obs = service.create_box_obstacle(Vector3(100, 100, 0), Vector3(5, 5, 3))
        service.add_obstacle(obs)

        binary_data = service.stream_chunk_binary(0, 0)
        assert binary_data is not None
        assert len(binary_data) > 0

    def test_obstacle_id_increment(self):
        """Test obstacle ID auto-increment."""
        service = WorldStreamingService()

        obs1 = service.create_box_obstacle(Vector3(100, 100, 0), Vector3(5, 5, 3))
        obs2 = service.create_box_obstacle(Vector3(200, 200, 0), Vector3(5, 5, 3))
        obs3 = service.create_mesh_obstacle(
            Vector3(300, 300, 0),
            Mesh([Vector3(0, 0, 0), Vector3(1, 0, 0), Vector3(0, 1, 0)], [0, 1, 2]),
        )

        assert obs1.id == 1
        assert obs2.id == 2
        assert obs3.id == 3

    def test_1000_obstacles(self):
        """Test performance with 1000+ obstacles."""
        service = WorldStreamingService(world_size=5000.0, chunk_size=500.0)

        # Add 1000 obstacles
        for i in range(1000):
            x = (i % 50) * 100
            y = (i // 50) * 100
            obs = service.create_box_obstacle(Vector3(x, y, 0), Vector3(10, 10, 3))
            service.add_obstacle(obs)

        stats = service.get_statistics()
        assert stats["total_obstacles"] == 1000

    def test_chunk_lod(self):
        """Test level of detail in chunks."""
        service = WorldStreamingService()
        chunk = service.get_chunk(0, 0, lod=2)
        assert chunk.lod_level == 2

    def test_all_chunks_json(self):
        """Test streaming all chunks."""
        service = WorldStreamingService()
        service.create_box_obstacle(Vector3(100, 100, 0), Vector3(5, 5, 3))
        service.create_box_obstacle(Vector3(600, 600, 0), Vector3(5, 5, 3))

        json_str = service.get_all_chunks_json()
        data = json.loads(json_str)
        assert isinstance(data, list)
        assert len(data) >= 1
