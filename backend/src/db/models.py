"""SQLAlchemy ORM models."""

from datetime import datetime

from sqlalchemy import JSON, BigInteger, Float, ForeignKey, Integer, String, Text, Boolean, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List, Optional, Any


class Base(DeclarativeBase):
    """SQLAlchemy declarative base."""

    pass


class User(Base):
    """User model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
    )

    # Relationships
    simulations: Mapped[List["Simulation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<User(id={self.id}, email={self.email})>"


class Scenario(Base):
    """Scenario model."""

    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    world_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
    )

    # Relationships
    simulations: Mapped[List["Simulation"]] = relationship(
        back_populates="scenario",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Scenario(id={self.id}, name={self.name})>"


class Simulation(Base):
    """Simulation model."""

    __tablename__ = "simulations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    scenario_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("scenarios.id", ondelete="SET NULL"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="created")
    num_agents: Mapped[int] = mapped_column(Integer, nullable=False)
    duration: Mapped[float] = mapped_column(Float, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column()
    completed_at: Mapped[Optional[datetime]] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=func.now(),
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="simulations")
    scenario: Mapped[Optional["Scenario"]] = relationship(back_populates="simulations")
    agents: Mapped[List["Agent"]] = relationship(
        back_populates="simulation",
        cascade="all, delete-orphan",
    )
    events: Mapped[List["Event"]] = relationship(
        back_populates="simulation",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Simulation(id={self.id}, name={self.name}, status={self.status})>"


class Agent(Base):
    """Agent model."""

    __tablename__ = "agents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    simulation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_type: Mapped[str] = mapped_column(String(50), default="vehicle")
    position_x: Mapped[float] = mapped_column(Float, nullable=False)
    position_y: Mapped[float] = mapped_column(Float, nullable=False)
    position_z: Mapped[float] = mapped_column(Float, default=0.0)
    velocity_x: Mapped[float] = mapped_column(Float, default=0.0)
    velocity_y: Mapped[float] = mapped_column(Float, default=0.0)
    velocity_z: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=func.now(),
    )

    # Relationships
    simulation: Mapped["Simulation"] = relationship(back_populates="agents")
    events: Mapped[List["Event"]] = relationship(
        back_populates="agent",
    )

    def __repr__(self) -> str:
        """String representation."""
        return f"<Agent(id={self.id}, simulation_id={self.simulation_id})>"


class Event(Base):
    """Event model."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    simulation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("simulations.id", ondelete="CASCADE"),
        nullable=False,
    )
    agent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("agents.id", ondelete="SET NULL"),
    )
    timestamp: Mapped[float] = mapped_column(Float, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        server_default=func.now(),
    )

    # Relationships
    simulation: Mapped["Simulation"] = relationship(back_populates="events")
    agent: Mapped[Optional["Agent"]] = relationship(back_populates="events")

    def __repr__(self) -> str:
        """String representation."""
        return f"<Event(id={self.id}, type={self.event_type}, ts={self.timestamp})>"
