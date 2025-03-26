import pandas as pd

# 1. SETUP

# Path to your CSV file
file_path = r"C:\TJ\pa_comm\Data.csv"

# Define the date range for January 2025
start_date = pd.to_datetime("2025-01-01")
end_date   = pd.to_datetime("2025-01-31")

# Define the payout table
payouts = {
    'ENT': {'A': 5000, 'B': 4000, 'C': 3000},
    'SMB': {'A': 2250, 'B': 1750, 'C': 1250},
    'MM':  {'A': 2500, 'B': 2000, 'C': 1500}
}

# Tier assignment function
def get_tier(num_showups):
    if num_showups >= 8:
        return 'A'
    elif num_showups >= 5:
        return 'B'
    elif num_showups >= 1:
        return 'C'
    else:
        return 'None'

# Company category function (ENT, MM, SMB) based on employee count
def get_company_category(emp_count):
    if emp_count >= 10000:
        return 'ENT'
    elif emp_count >= 1000:
        return 'MM'
    else:
        return 'SMB'

# 2. READ AND FILTER THE DATA

# Read the CSV
df = pd.read_csv(file_path)

# Convert 'Scheduled For' to datetime
df['Scheduled For'] = pd.to_datetime(df['Scheduled For'], errors='coerce')

# Filter rows for January 2025
df_jan = df[(df['Scheduled For'] >= start_date) & (df['Scheduled For'] <= end_date)]

# Filter rows where 'ShowedUp' is "Yes"
df_jan_showups = df_jan[df_jan['ShowedUp'].str.strip().str.lower() == "yes"]

# Convert 'Employee Count' to numeric
df_jan_showups['Employee Count'] = pd.to_numeric(df_jan_showups['Employee Count'], errors='coerce').fillna(0)

# Determine the company category for each showup
df_jan_showups['Category'] = df_jan_showups['Employee Count'].apply(get_company_category)

# 3. DETERMINE TOTAL SHOWUPS PER SDR & ASSIGN TIERS

# Count total showups per SDR (Name column)
sdr_totals = (
    df_jan_showups.groupby('Name', as_index=False)
    .size()
    .rename(columns={'size': 'Total_Showups'})
)

# Assign tier based on total showups
sdr_totals['Tier'] = sdr_totals['Total_Showups'].apply(get_tier)

# 4. CALCULATE SHOWUPS BY CATEGORY PER SDR

# Count how many showups each SDR has per category
sdr_category = (
    df_jan_showups.groupby(['Name', 'Category'], as_index=False)
    .size()
    .rename(columns={'size': 'Category_Showups'})
)

# Merge the total showups & tier onto the category breakdown
merged = pd.merge(sdr_category, sdr_totals, on='Name', how='left')

# 5. CALCULATE PAYOUT FOR EACH (SDR, CATEGORY)

def calculate_payout(row):
    tier = row['Tier']
    cat  = row['Category']
    num_showups = row['Category_Showups']
    
    # If the SDR has a recognized tier (A, B, C), get the correct payout
    if tier in ['A', 'B', 'C']:
        rate = payouts[cat][tier]
        return num_showups * rate
    else:
        # If no tier (0 showups), no payout
        return 0

merged['Payout'] = merged.apply(calculate_payout, axis=1)

# 6. CALCULATE THE TOTAL PAYOUT PER SDR

# We'll add a column that shows the total payout for each SDR
merged['Total_Payout'] = merged.groupby('Name')['Payout'].transform('sum')

# 7. FORMAT THE FINAL OUTPUT

# Reorder columns for clarity
final_cols = [
    'Name',
    'Total_Showups',
    'Tier',
    'Category',
    'Category_Showups',
    'Payout',
    'Total_Payout'
]
final_df = merged[final_cols].sort_values(by=['Name', 'Category'])

# 8. PRINT THE BREAKDOWN

print("\nDetailed Commission Breakdown (January 2025):")
print(final_df.to_string(index=False))

# 9. SAVE TO CSV IF NEEDED

output_path = r"C:\TJ\pa_comm\commission_breakdown.csv"
final_df.to_csv(output_path, index=False)
print(f"\nCommission breakdown saved to: {output_path}")
