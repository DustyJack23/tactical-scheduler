import pandas as pd
from io import StringIO
from datetime import timedelta
import streamlit as st
import pandas as pd
from io import StringIO
from datetime import timedelta
import streamlit as st

# Paste your data sample into a multiline string
data = '''Order	Item	Sch Ship	Line Item Price	Build Date
526687	2-0046-9999-DAIKIN RPS	6/9/2025	10912	6/9/2025
526687	2-0046-9999-DAIKIN RPS-1	6/9/2025	10912	6/9/2025
526687	9-0046-100-ER100	6/9/2025	0	6/9/2025
526687	9-0046-100-ER100	6/9/2025	0	6/9/2025
527202	1-2060-4000	6/9/2025	250	6/9/2025
... (cut rest for now) ...
'''

# Convert the data to a DataFrame
df = pd.read_csv(StringIO(data), sep="\t")

# Parse dates
df['Sch Ship'] = pd.to_datetime(df['Sch Ship'])
df['Build Date'] = pd.to_datetime(df['Build Date'])

# Daily totals
daily_totals = df.groupby('Build Date')['Line Item Price'].sum()

# Flag overages
capacity_limit = 70000
df['Overload'] = df['Build Date'].map(lambda d: daily_totals.get(d, 0) > capacity_limit)

# Schedule mapping
start_time = pd.to_datetime('05:00:00').time()
time_per_item = timedelta(minutes=30)

schedule = []
for date, group in df.groupby('Build Date'):
    current_time = pd.Timestamp.combine(date, start_time)
    for _, row in group.iterrows():
        schedule.append({
            'Build Date': date,
            'Order': row['Order'],
            'Item': row['Item'],
            'Time Slot': current_time.time(),
            'Line Item Price': row['Line Item Price'],
            'Overloaded': row['Overload']
        })
        current_time += time_per_item

schedule_df = pd.DataFrame(schedule)

# Summary
summary = schedule_df.groupby('Build Date').agg(
    Orders=('Order', 'nunique'),
    Total_Items=('Item', 'count'),
    Total_Revenue=('Line Item Price', 'sum'),
    Overloaded=('Overloaded', 'any')
).reset_index()

# UI
st.title("🚛 Tactical Schedule Viewer")

selected_date = st.date_input("Choose a Build Date", value=summary['Build Date'].min().date())
if selected_date:
    sel_data = schedule_df[schedule_df['Build Date'] == pd.Timestamp(selected_date)]
    st.subheader(f"Total Revenue for {selected_date}: ${sel_data['Line Item Price'].sum():,.2f}")
    st.dataframe(sel_data[['Time Slot', 'Order', 'Item', 'Line Item Price']])

st.subheader("📊 Weekly Summary")
st.dataframe(summary)
