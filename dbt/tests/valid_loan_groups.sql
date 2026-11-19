select group_id
from {{ ref('loan_groups') }}
group by group_id
having count(*) != 1 or sum(borrowers) != 5
