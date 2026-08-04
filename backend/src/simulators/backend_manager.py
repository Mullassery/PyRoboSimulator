"""Backend Manager - Handles simulator backend lifecycle and switching.

Manages the creation, configuration, and switching of simulator backends.
Implements dependency injection and factory patterns for clean architecture.
"""

import logging
from typing import Dict, Optional, Type

from backend.src.simulators.backend_interface import (
    SimulatorBackend,
    SimulatorConfig,
    SimulatorType,
)

logger = logging.getLogger(__name__)


class BackendFactory:
    """Factory for creating simulator backend instances."""

    def __init__(self):
        """Initialize factory."""
        self._backends: Dict[SimulatorType, Type[SimulatorBackend]] = {}

    def register_backend(
        self, simulator_type: SimulatorType, backend_class: Type[SimulatorBackend]
    ) -> None:
        """Register a backend implementation.

        Args:
            simulator_type: Simulator type identifier
            backend_class: Backend class (must inherit SimulatorBackend)

        Raises:
            ValueError: If backend_class is not a SimulatorBackend subclass
        """
        if not issubclass(backend_class, SimulatorBackend):
            raise ValueError(
                f"{backend_class} must be a subclass of SimulatorBackend"
            )

        self._backends[simulator_type] = backend_class
        logger.info(f"Registered backend: {simulator_type.value} -> {backend_class.__name__}")

    def create_backend(self, config: SimulatorConfig) -> SimulatorBackend:
        """Create a backend instance.

        Args:
            config: Simulator configuration

        Returns:
            Backend instance

        Raises:
            ValueError: If simulator type not registered
        """
        backend_class = self._backends.get(config.simulator_type)

        if not backend_class:
            raise ValueError(
                f"Backend not registered: {config.simulator_type.value}. "
                f"Available: {list(self._backends.keys())}"
            )

        logger.info(f"Creating backend: {config.simulator_type.value}")
        return backend_class()

    def is_registered(self, simulator_type: SimulatorType) -> bool:
        """Check if backend is registered.

        Args:
            simulator_type: Simulator type

        Returns:
            True if registered
        """
        return simulator_type in self._backends

    def get_registered_backends(self) -> Dict[SimulatorType, Type[SimulatorBackend]]:
        """Get all registered backends.

        Returns:
            Dictionary of registered backends
        """
        return dict(self._backends)


class BackendManager:
    """Manages active simulator backend and switching.

    Handles:
    - Backend lifecycle (init, shutdown)
    - Hot-swapping between simulators
    - State preservation during switches
    - Configuration management
    """

    def __init__(self, factory: Optional[BackendFactory] = None):
        """Initialize manager.

        Args:
            factory: Backend factory (creates one if not provided)
        """
        self._factory = factory or BackendFactory()
        self._current_backend: Optional[SimulatorBackend] = None
        self._config: Optional[SimulatorConfig] = None
        self._initialized = False

    def initialize(self, config: SimulatorConfig) -> SimulatorBackend:
        """Initialize a simulator backend.

        Args:
            config: Simulator configuration

        Returns:
            Initialized backend

        Raises:
            RuntimeError: If backend already initialized
            ValueError: If config invalid
        """
        if self._initialized and self._current_backend:
            raise RuntimeError("Backend already initialized. Call shutdown() first.")

        logger.info(f"Initializing backend: {config.simulator_type.value}")

        # Create backend instance
        backend = self._factory.create_backend(config)

        # Validate configuration
        if not backend.validate_configuration(config):
            raise ValueError(f"Invalid configuration for {config.simulator_type.value}")

        # Initialize backend
        backend.initialize(config)

        self._current_backend = backend
        self._config = config
        self._initialized = True

        logger.info(f"Backend initialized successfully: {config.simulator_type.value}")
        return backend

    def shutdown(self) -> None:
        """Shutdown current backend.

        Raises:
            RuntimeError: If no backend initialized
        """
        if not self._current_backend:
            raise RuntimeError("No backend initialized")

        logger.info(f"Shutting down backend: {self._config.simulator_type.value}")
        self._current_backend.shutdown()

        self._current_backend = None
        self._config = None
        self._initialized = False

    def switch_backend(self, new_config: SimulatorConfig) -> SimulatorBackend:
        """Switch to a different simulator backend.

        Shutdown current backend and initialize new one.

        Args:
            new_config: New simulator configuration

        Returns:
            New backend instance

        Raises:
            RuntimeError: If switch fails
        """
        if self._initialized and self._current_backend:
            logger.info(
                f"Switching from {self._config.simulator_type.value} "
                f"to {new_config.simulator_type.value}"
            )
            self.shutdown()

        return self.initialize(new_config)

    def get_backend(self) -> SimulatorBackend:
        """Get current backend.

        Returns:
            Current backend

        Raises:
            RuntimeError: If no backend initialized
        """
        if not self._current_backend:
            raise RuntimeError("No backend initialized")

        return self._current_backend

    def is_initialized(self) -> bool:
        """Check if backend is initialized.

        Returns:
            True if initialized
        """
        return self._initialized and self._current_backend is not None

    def get_current_simulator_type(self) -> Optional[SimulatorType]:
        """Get current simulator type.

        Returns:
            Current simulator type or None
        """
        if self._current_backend:
            return self._current_backend.get_simulator_type()

        return None

    def get_config(self) -> Optional[SimulatorConfig]:
        """Get current configuration.

        Returns:
            Current config or None
        """
        return self._config

    def register_backend(
        self, simulator_type: SimulatorType, backend_class: Type[SimulatorBackend]
    ) -> None:
        """Register a backend implementation.

        Args:
            simulator_type: Simulator type
            backend_class: Backend class
        """
        self._factory.register_backend(simulator_type, backend_class)

    def is_backend_registered(self, simulator_type: SimulatorType) -> bool:
        """Check if backend is registered.

        Args:
            simulator_type: Simulator type

        Returns:
            True if registered
        """
        return self._factory.is_registered(simulator_type)

    def get_registered_backends(self) -> Dict[SimulatorType, Type[SimulatorBackend]]:
        """Get all registered backends.

        Returns:
            Dictionary of registered backends
        """
        return self._factory.get_registered_backends()


class BackendContext:
    """Context manager for backend lifecycle management.

    Usage:
        config = SimulatorConfig(...)
        with BackendContext(config) as backend:
            backend.spawn_robot(...)
            backend.step()
    """

    def __init__(
        self, config: SimulatorConfig, factory: Optional[BackendFactory] = None
    ):
        """Initialize context.

        Args:
            config: Simulator configuration
            factory: Backend factory
        """
        self._config = config
        self._factory = factory or BackendFactory()
        self._manager = BackendManager(self._factory)
        self._backend: Optional[SimulatorBackend] = None

    def __enter__(self) -> SimulatorBackend:
        """Enter context, initialize backend.

        Returns:
            Initialized backend
        """
        self._backend = self._manager.initialize(self._config)
        return self._backend

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context, shutdown backend.

        Args:
            exc_type: Exception type if error occurred
            exc_val: Exception value
            exc_tb: Exception traceback
        """
        if self._manager.is_initialized():
            self._manager.shutdown()

        if exc_type is not None:
            logger.error(f"Error in backend context: {exc_val}")

        return False  # Don't suppress exceptions
