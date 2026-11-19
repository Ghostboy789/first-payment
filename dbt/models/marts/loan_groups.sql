select group_id, block_id, assigned_grace, count(*) as borrowers
from {{ ref('borrowers') }}
group by group_id, block_id, assigned_grace
