"""Add amendment tracking and remove URL unique constraint

Revision ID: 65d8cb20ba20
Revises: 6fc9e2501bb1
Create Date: 2025-11-29 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '65d8cb20ba20'
down_revision = '6fc9e2501bb1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    
    if is_sqlite:
        # SQLite: Recreate table without unique constraint on url
        # Clean up any leftover table from previous failed migration
        op.execute("DROP TABLE IF EXISTS opportunities_new")
        
        # Step 1: Create new table structure
        op.create_table('opportunities_new',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('opportunity_code', sa.String(), nullable=False),
            sa.Column('opportunity_type', sa.String(), nullable=True),
            sa.Column('nato_body', sa.String(), nullable=True),
            sa.Column('opportunity_name', sa.String(), nullable=False),
            sa.Column('url', sa.String(), nullable=False),  # No unique constraint
            sa.Column('pdf_url', sa.String(), nullable=True),
            sa.Column('source_url', sa.String(), nullable=True),
            sa.Column('contract_type', sa.String(), nullable=True),
            sa.Column('document_classification', sa.String(), nullable=True),
            sa.Column('response_classification', sa.String(), nullable=True),
            sa.Column('contract_duration', sa.String(), nullable=True),
            sa.Column('currency', sa.String(), nullable=True),
            sa.Column('eligible_organization_types', sa.Text(), nullable=True),
            sa.Column('clarification_deadline', sa.String(), nullable=True),
            sa.Column('clarification_instructions', sa.Text(), nullable=True),
            sa.Column('bid_closing_date', sa.String(), nullable=True),
            sa.Column('expected_contract_award_date', sa.String(), nullable=True),
            sa.Column('bid_validity_days', sa.Integer(), nullable=True),
            sa.Column('clarification_deadline_parsed', sa.DateTime(), nullable=True),
            sa.Column('bid_closing_date_parsed', sa.DateTime(), nullable=True),
            sa.Column('expected_contract_award_date_parsed', sa.DateTime(), nullable=True),
            sa.Column('required_documents', sa.Text(), nullable=True),
            sa.Column('proposal_content', sa.Text(), nullable=True),
            sa.Column('submission_instructions', sa.Text(), nullable=True),
            sa.Column('evaluation_criteria', sa.String(), nullable=True),
            sa.Column('evaluation_criteria_full', sa.Text(), nullable=True),
            sa.Column('bid_compliance_criteria', sa.Text(), nullable=True),
            sa.Column('partial_bidding_allowed', sa.Boolean(), nullable=True),
            sa.Column('contact_person', sa.String(), nullable=True),
            sa.Column('contact_email', sa.String(), nullable=True),
            sa.Column('summary', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
            sa.Column('last_checked_at', sa.DateTime(), nullable=True),
            sa.Column('opportunity_posted_date', sa.DateTime(), nullable=True),
            sa.Column('extracted_at', sa.DateTime(), nullable=True),
            sa.Column('content_hash', sa.String(), nullable=True),
            sa.Column('last_content_update', sa.DateTime(), nullable=True),
            sa.Column('update_count', sa.Integer(), nullable=False),
            sa.Column('last_changed_fields', sa.JSON(), nullable=True),
            sa.Column('removed_at', sa.DateTime(), nullable=True),
            # New amendment tracking fields
            sa.Column('amendment_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('has_amendments', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('last_amendment_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('opportunity_code')
        )
        
        # Step 2: Copy data (explicitly list all columns)
        op.execute("""
            INSERT INTO opportunities_new (
                id, opportunity_code, opportunity_type, nato_body, opportunity_name, url, pdf_url, source_url,
                contract_type, document_classification, response_classification, contract_duration, currency,
                eligible_organization_types, clarification_deadline, clarification_instructions, bid_closing_date,
                expected_contract_award_date, bid_validity_days, clarification_deadline_parsed, bid_closing_date_parsed,
                expected_contract_award_date_parsed, required_documents, proposal_content, submission_instructions,
                evaluation_criteria, evaluation_criteria_full, bid_compliance_criteria, partial_bidding_allowed,
                contact_person, contact_email, summary, is_active, created_at, updated_at, last_checked_at,
                opportunity_posted_date, extracted_at, content_hash, last_content_update, update_count,
                last_changed_fields, removed_at, amendment_count, has_amendments, last_amendment_at
            )
            SELECT 
                id, opportunity_code, opportunity_type, nato_body, opportunity_name, url, pdf_url, source_url,
                contract_type, document_classification, response_classification, contract_duration, currency,
                eligible_organization_types, clarification_deadline, clarification_instructions, bid_closing_date,
                expected_contract_award_date, bid_validity_days, clarification_deadline_parsed, bid_closing_date_parsed,
                expected_contract_award_date_parsed, required_documents, proposal_content, submission_instructions,
                evaluation_criteria, evaluation_criteria_full, bid_compliance_criteria, partial_bidding_allowed,
                contact_person, contact_email, summary, is_active, created_at, updated_at, last_checked_at,
                opportunity_posted_date, extracted_at, content_hash, last_content_update, update_count,
                last_changed_fields, removed_at, 0, 0, NULL
            FROM opportunities
        """)
        
        # Step 3: Drop old table and rename new one
        op.drop_table('opportunities')
        op.rename_table('opportunities_new', 'opportunities')
        
        # Step 4: Recreate indexes
        op.create_index('ix_opportunities_opportunity_code', 'opportunities', ['opportunity_code'], unique=True)
        op.create_index('ix_opportunities_bid_closing_date_parsed', 'opportunities', ['bid_closing_date_parsed'])
        op.create_index('ix_opportunities_clarification_deadline_parsed', 'opportunities', ['clarification_deadline_parsed'])
        op.create_index('ix_opportunities_content_hash', 'opportunities', ['content_hash'])
        op.create_index('ix_opportunities_is_active', 'opportunities', ['is_active'])
        op.create_index('ix_opportunities_last_content_update', 'opportunities', ['last_content_update'])
        op.create_index('ix_opportunities_nato_body', 'opportunities', ['nato_body'])
        op.create_index('ix_opportunities_opportunity_posted_date', 'opportunities', ['opportunity_posted_date'])
        op.create_index('ix_opportunities_opportunity_type', 'opportunities', ['opportunity_type'])
    else:
        # PostgreSQL/Other: Standard operations
        # Drop unique constraint
        from sqlalchemy import inspect
        inspector = inspect(bind)
        constraints = inspector.get_unique_constraints('opportunities')
        for constraint in constraints:
            if 'url' in constraint['column_names']:
                op.drop_constraint(constraint['name'], 'opportunities', type_='unique')
                break
        
        # Add columns
        op.add_column('opportunities', sa.Column('amendment_count', sa.Integer(), nullable=False, server_default='0'))
        op.add_column('opportunities', sa.Column('has_amendments', sa.Boolean(), nullable=False, server_default='false'))
        op.add_column('opportunities', sa.Column('last_amendment_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    is_sqlite = bind.dialect.name == 'sqlite'
    
    if is_sqlite:
        with op.batch_alter_table('opportunities', schema=None) as batch_op:
            batch_op.drop_column('last_amendment_at')
            batch_op.drop_column('has_amendments')
            batch_op.drop_column('amendment_count')
            # Restore unique constraint via table recreation
            batch_op.create_unique_constraint('opportunities_url_key', ['url'])
    else:
        op.drop_column('opportunities', 'last_amendment_at')
        op.drop_column('opportunities', 'has_amendments')
        op.drop_column('opportunities', 'amendment_count')
        op.create_unique_constraint('opportunities_url_key', 'opportunities', ['url'])

