"""add_foreign_keys_and_relationships

Revision ID: 5128a15b9f50
Revises: b8cd4982360d
Create Date: 2026-09-18 01:08:25.213075
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5128a15b9f50'
down_revision: Union[str, None] = 'b8cd4982360d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('financial_transactions', sa.Column('user_id', sa.Integer(), nullable=True))
    op.alter_column('financial_transactions', 'invoice_id',
               existing_type=sa.VARCHAR(length=32),
               nullable=True)
    op.create_index(op.f('ix_financial_transactions_invoice_id'), 'financial_transactions', ['invoice_id'], unique=False)
    op.create_index(op.f('ix_financial_transactions_user_id'), 'financial_transactions', ['user_id'], unique=False)

    # Clean up dangling references so foreign keys succeed
    op.execute("UPDATE financial_transactions SET invoice_id = NULL WHERE invoice_id IS NOT NULL AND invoice_id NOT IN (SELECT id FROM invoices)")

    op.create_foreign_key('fk_financial_transactions_user_id', 'financial_transactions', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_financial_transactions_invoice_id', 'financial_transactions', 'invoices', ['invoice_id'], ['id'])
    op.add_column('ledger_entries', sa.Column('transaction_id', sa.String(length=32), nullable=True))
    op.create_index(op.f('ix_ledger_entries_transaction_id'), 'ledger_entries', ['transaction_id'], unique=False)

    op.execute("UPDATE ledger_entries SET journal_entry_id = NULL WHERE journal_entry_id IS NOT NULL AND journal_entry_id NOT IN (SELECT id FROM journal_entries)")

    op.create_foreign_key('fk_ledger_entries_transaction_id', 'ledger_entries', 'financial_transactions', ['transaction_id'], ['id'])
    op.create_foreign_key('fk_ledger_entries_journal_entry_id', 'ledger_entries', 'journal_entries', ['journal_entry_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_ledger_entries_journal_entry_id', 'ledger_entries', type_='foreignkey')
    op.drop_constraint('fk_ledger_entries_transaction_id', 'ledger_entries', type_='foreignkey')
    op.drop_index(op.f('ix_ledger_entries_transaction_id'), table_name='ledger_entries')
    op.drop_column('ledger_entries', 'transaction_id')
    op.drop_constraint('fk_financial_transactions_invoice_id', 'financial_transactions', type_='foreignkey')
    op.drop_constraint('fk_financial_transactions_user_id', 'financial_transactions', type_='foreignkey')
    op.drop_index(op.f('ix_financial_transactions_user_id'), table_name='financial_transactions')
    op.drop_index(op.f('ix_financial_transactions_invoice_id'), table_name='financial_transactions')
    op.alter_column('financial_transactions', 'invoice_id',
               existing_type=sa.VARCHAR(length=32),
               nullable=False)
    op.drop_column('financial_transactions', 'user_id')
