"""add wechat message receipts

Revision ID: 7c3d9f2a1b04
Revises: 4a1c2e9d7f01
Create Date: 2026-08-25 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "7c3d9f2a1b04"
down_revision: Union[str, None] = "4a1c2e9d7f01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wechatmessagereceipt",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dedupe_key", sa.String(), nullable=False),
        sa.Column("message_id", sa.String(), nullable=False),
        sa.Column("nonce", sa.String(), nullable=False),
        sa.Column("received_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("dedupe_key"),
    )
    with op.batch_alter_table("wechatmessagereceipt", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_wechatmessagereceipt_dedupe_key"), ["dedupe_key"], unique=True)
        batch_op.create_index(batch_op.f("ix_wechatmessagereceipt_message_id"), ["message_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_wechatmessagereceipt_nonce"), ["nonce"], unique=False)
        batch_op.create_index(batch_op.f("ix_wechatmessagereceipt_received_at"), ["received_at"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("wechatmessagereceipt", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_wechatmessagereceipt_received_at"))
        batch_op.drop_index(batch_op.f("ix_wechatmessagereceipt_nonce"))
        batch_op.drop_index(batch_op.f("ix_wechatmessagereceipt_message_id"))
        batch_op.drop_index(batch_op.f("ix_wechatmessagereceipt_dedupe_key"))
    op.drop_table("wechatmessagereceipt")
