"""Create initial database schema

Revision ID: 001_create_initial_schema
Revises:
Create Date: 2024-07-29

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001_create_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial tables."""

    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_users_email', 'users', ['email'])

    # Scenarios table
    op.create_table(
        'scenarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('world_config', sa.JSON(), nullable=False),
        sa.Column('published', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_scenarios_published', 'scenarios', ['published'])
    op.create_index('idx_scenarios_created_at', 'scenarios', ['created_at'])

    # Simulations table
    op.create_table(
        'simulations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='created'),
        sa.Column('num_agents', sa.Integer(), nullable=False),
        sa.Column('duration', sa.Float(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_simulations_user_id', 'simulations', ['user_id'])
    op.create_index('idx_simulations_status', 'simulations', ['status'])
    op.create_index('idx_simulations_created_at', 'simulations', ['created_at', 'id'])
    op.create_index('idx_simulations_scenario_id', 'simulations', ['scenario_id'])

    # Agents table
    op.create_table(
        'agents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('simulation_id', sa.Integer(), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False, server_default='vehicle'),
        sa.Column('position_x', sa.Float(), nullable=False),
        sa.Column('position_y', sa.Float(), nullable=False),
        sa.Column('position_z', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('velocity_x', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('velocity_y', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('velocity_z', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_agents_simulation_id', 'agents', ['simulation_id'])
    # Spatial index for position queries (PostGIS would use GIST here)
    op.create_index('idx_agents_position_x', 'agents', ['position_x'])
    op.create_index('idx_agents_position_y', 'agents', ['position_y'])

    # Events table (high volume)
    op.create_table(
        'events',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('simulation_id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('data', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['simulation_id'], ['simulations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    # Events indexed by simulation and timestamp (critical for result queries)
    op.create_index(
        'idx_events_simulation_timestamp',
        'events',
        ['simulation_id', 'timestamp']
    )
    op.create_index('idx_events_agent_id', 'events', ['agent_id'])
    op.create_index('idx_events_event_type', 'events', ['event_type'])


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('events')
    op.drop_table('agents')
    op.drop_table('simulations')
    op.drop_table('scenarios')
    op.drop_table('users')
