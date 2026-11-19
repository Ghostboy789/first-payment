select
    borrower_id::integer as borrower_id,
    group_id,
    block_id::integer as block_id,
    assigned_grace::integer as assigned_grace,
    loan_size,
    loan_use_flag,
    age::double as age,
    married::double as married,
    education::double as education,
    household_size::double as household_size,
    baseline_business::double as baseline_business,
    survey3_income_recorded
from {{ ref('stg_replication') }}
