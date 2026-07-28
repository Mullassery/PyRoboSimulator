"""Tests for FastAPI backend."""

import json
import pytest
from fastapi.testclient import TestClient

from ..api import create_app
from ..schemas import WorldSpec, ObjectDefinition, MaterialType, RenderingProfile


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestHealthAndRoot:
    """Test basic endpoints."""

    def test_health_check(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "PyRoboSimulator" in data["service"]


class TestLoadWorld:
    """Test world loading endpoint."""

    def test_load_world(self, client):
        spec = WorldSpec(
            metadata={"name": "test_world"},
        )

        response = client.post(
            "/api/v1/load-world",
            json={
                "spec": json.loads(spec.model_dump_json()),
                "world_id": "test_world_1",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["world_id"] == "test_world_1"
        assert data["status"] == "loaded"

    def test_load_world_with_objects(self, client):
        spec = WorldSpec(
            metadata={"name": "parking_lot"},
            objects=[
                ObjectDefinition(
                    id="car_1",
                    name="Car",
                    position=(10.0, 20.0, 0.5),
                    material=MaterialType.METAL,
                )
            ],
        )

        response = client.post(
            "/api/v1/load-world",
            json={
                "spec": json.loads(spec.model_dump_json()),
            },
        )

        assert response.status_code == 200
        world_id = response.json()["world_id"]
        assert world_id is not None

    def test_load_world_auto_generates_id(self, client):
        spec = WorldSpec()

        response = client.post(
            "/api/v1/load-world",
            json={"spec": json.loads(spec.model_dump_json())},
        )

        assert response.status_code == 200
        world_id = response.json()["world_id"]
        assert world_id is not None


class TestGetWorld:
    """Test world retrieval endpoint."""

    def test_get_loaded_world(self, client):
        spec = WorldSpec(
            metadata={"name": "test_world"},
        )

        load_resp = client.post(
            "/api/v1/load-world",
            json={
                "spec": json.loads(spec.model_dump_json()),
                "world_id": "world_1",
            },
        )
        assert load_resp.status_code == 200

        get_resp = client.get("/api/v1/worlds/world_1")
        assert get_resp.status_code == 200
        assert get_resp.json()["metadata"]["name"] == "test_world"

    def test_get_nonexistent_world(self, client):
        response = client.get("/api/v1/worlds/nonexistent")
        assert response.status_code == 404


class TestSensorData:
    """Test sensor data endpoints."""

    def test_get_rgb_sensor(self, client):
        spec = WorldSpec(
            metadata={"name": "sensor_test"},
        )

        client.post(
            "/api/v1/load-world",
            json={
                "spec": json.loads(spec.model_dump_json()),
                "world_id": "world_1",
            },
        )

        response = client.get("/api/v1/sensors/world_1/rgb")
        assert response.status_code == 200
        data = response.json()
        assert data["sensor_type"] == "rgb"
        assert data["world_id"] == "world_1"
        assert "data_path" in data
        assert "preview" in data
        assert data["preview"]["format"] == "png"

    def test_get_depth_sensor(self, client):
        spec = WorldSpec()

        client.post(
            "/api/v1/load-world",
            json={
                "spec": json.loads(spec.model_dump_json()),
                "world_id": "world_1",
            },
        )

        response = client.get("/api/v1/sensors/world_1/depth")
        assert response.status_code == 200
        data = response.json()
        assert data["sensor_type"] == "depth"
        assert data["preview"]["format"] == "npy"

    def test_get_lidar_sensor(self, client):
        spec = WorldSpec()

        client.post(
            "/api/v1/load-world",
            json={
                "spec": json.loads(spec.model_dump_json()),
                "world_id": "world_1",
            },
        )

        response = client.get("/api/v1/sensors/world_1/lidar")
        assert response.status_code == 200
        data = response.json()
        assert data["sensor_type"] == "lidar"
        assert data["preview"]["channels"] == 16

    def test_get_thermal_sensor(self, client):
        spec = WorldSpec()

        client.post(
            "/api/v1/load-world",
            json={
                "spec": json.loads(spec.model_dump_json()),
                "world_id": "world_1",
            },
        )

        response = client.get("/api/v1/sensors/world_1/thermal")
        assert response.status_code == 200
        data = response.json()
        assert data["sensor_type"] == "thermal"

    def test_invalid_sensor_type(self, client):
        spec = WorldSpec()

        client.post(
            "/api/v1/load-world",
            json={
                "spec": json.loads(spec.model_dump_json()),
                "world_id": "world_1",
            },
        )

        response = client.get("/api/v1/sensors/world_1/invalid_sensor")
        assert response.status_code == 400

    def test_sensor_nonexistent_world(self, client):
        response = client.get("/api/v1/sensors/nonexistent/rgb")
        assert response.status_code == 404

    def test_sensor_with_frame_number(self, client):
        spec = WorldSpec()

        client.post(
            "/api/v1/load-world",
            json={
                "spec": json.loads(spec.model_dump_json()),
                "world_id": "world_1",
            },
        )

        response = client.get("/api/v1/sensors/world_1/rgb?frame=42")
        assert response.status_code == 200
        data = response.json()
        assert "frame_0042" in data["data_path"]


class TestGenerateWorld:
    """Test world generation endpoint (Claude integration)."""

    def test_generate_world_endpoint_exists(self, client):
        """Test endpoint is available (actual generation requires API key)."""
        request_data = {
            "prompt": "A simple parking lot",
        }

        response = client.post("/api/v1/generate-world", json=request_data)

        assert response.status_code in [200, 400, 401, 403, 500]

    def test_generate_world_request_validation(self, client):
        """Test request validation."""
        response = client.post("/api/v1/generate-world", json={})
        assert response.status_code in [400, 422]
