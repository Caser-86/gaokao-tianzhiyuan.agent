"""add chat session persistence

Revision ID: 4a1c2e9d7f01
Revises: e7780a90b130
Create Date: 2026-08-25 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4a1c2e9d7f01"
down_revision: Union[str, None] = "e7780a90b130"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "chatsession",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", name="uq_chat_sessions_session_id"),
    )
    with op.batch_alter_table("chatsession", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_chatsession_channel"), ["channel"], unique=False)
        batch_op.create_index(batch_op.f("ix_chatsession_expires_at"), ["expires_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_chatsession_session_id"), ["session_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_chatsession_user_id"), ["user_id"], unique=False)

    op.create_table(
        "chatmessage",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["chatsession.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("chatmessage", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_chatmessage_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_chatmessage_role"), ["role"], unique=False)
        batch_op.create_index(batch_op.f("ix_chatmessage_request_id"), ["request_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_chatmessage_session_id"), ["session_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("chatmessage", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_chatmessage_session_id"))
        batch_op.drop_index(batch_op.f("ix_chatmessage_request_id"))
        batch_op.drop_index(batch_op.f("ix_chatmessage_role"))
        batch_op.drop_index(batch_op.f("ix_chatmessage_created_at"))
    op.drop_table("chatmessage")

    with op.batch_alter_table("chatsession", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_chatsession_user_id"))
        batch_op.drop_index(batch_op.f("ix_chatsession_session_id"))
        batch_op.drop_index(batch_op.f("ix_chatsession_expires_at"))
        batch_op.drop_index(batch_op.f("ix_chatsession_channel"))
    op.drop_table("chatsession")
