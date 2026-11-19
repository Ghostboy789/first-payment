select
    borrower_id::integer as borrower_id,
    default_52w::double as default_52w,
    outstanding_52w::double as outstanding_52w,
    investment::double as investment,
    profit::double as profit,
    (profit is not null)::integer as profit_recorded
from {{ ref('stg_replication') }}
