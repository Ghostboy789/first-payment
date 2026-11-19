select block_id
from {{ ref('loan_groups') }}
group by block_id
having count(distinct assigned_grace) != 2
