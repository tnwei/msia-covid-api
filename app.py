from chalice import Chalice
import pandas as pd
import logging

app = Chalice(app_name='msia-covid-data')

# Download links, obtained from inspecting the download link when exporting from Google Docs
# Google Docs link:
source_gdoc = "https://docs.google.com/spreadsheets/d/15A43eb68LT7gg_k9VavYwS1R2KkCTpvigYMn5KT9RTM/"

# Export as Excel
# https://docs.google.com/spreadsheets/d/15A43eb68LT7gg_k9VavYwS1R2KkCTpvigYMn5KT9RTM/export?format=xlsx&id=15A43eb68LT7gg_k9VavYwS1R2KkCTpvigYMn5KT9RTM
# 
# Export Base sheet as CSV
national_csv_url = "https://docs.google.com/spreadsheets/d/15A43eb68LT7gg_k9VavYwS1R2KkCTpvigYMn5KT9RTM/export?format=csv&id=15A43eb68LT7gg_k9VavYwS1R2KkCTpvigYMn5KT9RTM&gid=0"
# 
# Export State sheet as CSV
states_csv_url = "https://docs.google.com/spreadsheets/d/15A43eb68LT7gg_k9VavYwS1R2KkCTpvigYMn5KT9RTM/export?format=csv&id=15A43eb68LT7gg_k9VavYwS1R2KkCTpvigYMn5KT9RTM&gid=1863753353"
# 
# Export Death cases sheet as CSV
# https://docs.google.com/spreadsheets/d/15A43eb68LT7gg_k9VavYwS1R2KkCTpvigYMn5KT9RTM/export?format=csv&id=15A43eb68LT7gg_k9VavYwS1R2KkCTpvigYMn5KT9RTM&gid=41230890

@app.route('/latest/national')
def retrieve_national():
    try:
        nat = pd.read_csv(national_csv_url)
        logging.info('Retrieve Google Doc OK!')

        # Remove blank dates
        # Prevent NaT's making the indices no longer monotonic
        nat = nat.dropna(subset=['Date'], how='any')
        nat = nat.set_index('Date')

        # Rename and keep only columns of interest
        nat = nat.rename(columns={
            'Positive': 'confirmed_cases',
            'Death': 'fatalities',
            'Discharged': 'recovered',
            'Active': 'active'
        })
        nat = nat[['confirmed_cases', 'fatalities', 'recovered', 'active']]

        # Calculate more columns of interest
        nat['daily_change'] = nat['confirmed_cases'].diff()

        # Drop pre-filled dates that do not have data yet
        nat = nat.dropna(axis='rows', how='all')

        logging.info('DataFrame processing OK!')

        # Read by doing pd.read_json(URL)
        # Datetime index is automatic!
        return nat.to_json()
    except Exception as e:
        return f'{e} raised, something went wrong! Go to the source and grab data manually at {source_gdoc}'

@app.route('/latest/states')
def retrieve_states():
    try:
        states = pd.read_csv(states_csv_url)
        logging.info('Retrieve Google Doc OK!')

        # Remove blank dates
        # Prevent NaT's making the indices no longer monotonic
        states = states.dropna(subset=['Date'], how='any')
        states = states.set_index('Date')

        # Drop pre-filled dates that do not have data yet
        states = states.dropna(axis='rows', how='all')

        # Only keep required info
        # Original sheet has redundant information!
        keep_cols = ['Perlis', 'Kedah', 'Pulau Pinang', 'Perak', 'Selangor', 'Negeri Sembilan',
        'Melaka', 'Johor', 'Pahang', 'Terengganu',
        'Kelantan', 'Sabah', 'Sarawak', 'WP Labuan', 'WP Kuala Lumpur',
        'WP Putrajaya']

        states = states[keep_cols]

        logging.info('DataFrame processing OK!')

        # Read by doing pd.read_json(URL)
        # Datetime index is automatic!
        return states.to_json()
    except Exception as e:
        return f'{e} raised, something went wrong! Go to the source and grab data manually at {source_gdoc}'
