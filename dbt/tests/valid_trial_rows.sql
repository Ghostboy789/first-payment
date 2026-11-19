select borrower_id
from {{ ref('stg_replication') }}
where borrower_id is null or group_id is null or trim(group_id) = ''
    or block_id is null or block_id != trunc(block_id)
    or assigned_grace is null or assigned_grace not in (0, 1)
    or loan_size is null or loan_size <= 0
    or loan_use_flag is null or loan_use_flag not in (0, 1)
    or default_52w is null or default_52w not in (0, 1)
    or outstanding_52w is null or not isfinite(outstanding_52w) or outstanding_52w < 0
    or investment is null or not isfinite(investment)
    or (profit is not null and (not isfinite(profit) or not survey3_income_recorded))
