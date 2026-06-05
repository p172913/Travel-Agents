"""Initial TravelSouls schema

Revision ID: 001
Revises:
Create Date: 2026-06-05

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_table(
        "preferences",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("budget_tier", sa.String(50)),
        sa.Column("dietary_preferences", sa.JSON()),
        sa.Column("travel_style", sa.JSON()),
        sa.Column("interests", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
        sa.Column("updated_at", sa.DateTime()),
    )
    op.create_table(
        "trips",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("destination", sa.String(255), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("budget_limit", sa.Float(), nullable=False),
        sa.Column("status", sa.String(50)),
        sa.Column("share_token", sa.String(36), unique=True),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "trip_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50)),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "trip_plans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="CASCADE"), nullable=False),
        sa.Column("itinerary", sa.JSON(), nullable=False),
        sa.Column("budget_breakdown", sa.JSON(), nullable=False),
        sa.Column("explanation", sa.Text()),
        sa.Column("recommendations", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_plan_id", sa.Integer(), sa.ForeignKey("trip_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("booking_reference", sa.String(100)),
        sa.Column("status", sa.String(50)),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "agent_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_id", sa.Integer(), sa.ForeignKey("trips.id", ondelete="SET NULL")),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("message", sa.Text()),
        sa.Column("input_data", sa.JSON()),
        sa.Column("output_data", sa.JSON()),
        sa.Column("created_at", sa.DateTime()),
    )
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trip_plan_id", sa.Integer(), sa.ForeignKey("trip_plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_type", sa.String(50), nullable=False),
        sa.Column("item_id", sa.String(100), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comments", sa.Text()),
        sa.Column("created_at", sa.DateTime()),
    )


def downgrade() -> None:
    op.drop_table("feedback")
    op.drop_table("agent_logs")
    op.drop_table("bookings")
    op.drop_table("trip_plans")
    op.drop_table("trip_requests")
    op.drop_table("trips")
    op.drop_table("preferences")
    op.drop_table("users")
