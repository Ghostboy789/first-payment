select
    slid as borrower_id,
    sec_group_name as group_id,
    Stratification_Dummies as block_id,
    sec_treat as assigned_grace,
    sec_loanamount as loan_size,
    Match3rd_in3rd as loan_use_flag,
    not_finished_aug19 as default_52w,
    Outstanding_Loan_Amount_Default as outstanding_52w,
    Business_Expenditures as investment,
    Profit as profit,
    "Income" is not null as survey3_income_recorded,
    case when miss_Age_C = 0 then Age_C end as age,
    case when miss_Married_C = 0 then Married_C end as married,
    case when miss_Years_Education_C = 0 then Years_Education_C end as education,
    case when miss_HH_Size_C = 0 then HH_Size_C end as household_size,
    case when miss_Has_Business_C = 0 then Has_Business_C end as baseline_business
from read_parquet('{{ env_var("FIRST_PAYMENT_PARQUET_PATH", "data/replication.parquet") | replace("'", "''") }}')
