from timeit import default_timer as timer

start_init_timer = timer()

import tempfile
from pathlib import Path
import datetime
from enum import Enum

from typing import Optional
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import pandas as pd
import numpy as np
import git

# Constants
MOHREPO_URL = "https://github.com/MoH-Malaysia/covid19-public"
CITFREPO_URL = "https://github.com/CITF-Malaysia/citf-public"

app = FastAPI()

## Retrieve data to memory -------------------------------

# Setup temp dirs
# Cleans up nicely when FastAPI restarts or shuts down
# Instead of figuring out data persistence, easier to clone
# to memory on startup for a small app like this
mohdirobj = tempfile.TemporaryDirectory()
mohdir_fp = Path(mohdirobj.name)
citfdirobj = tempfile.TemporaryDirectory()
citfdir_fp = Path(citfdirobj.name)

print(f"{timer() - start_init_timer:5.1f}s: Temp path created at {mohdirobj.name}")


def pprint_time(total_seconds):
    # Less than an hour
    if total_seconds < 3600:
        return f"{int(total_seconds//60)}m ago"
    # Less than a day
    elif total_seconds < 86400:
        minutes = (total_seconds // 60) % 60
        hours = (total_seconds // 60) // 60
        return f"{int(hours)}h {int(minutes)}m ago"
    # More than a day
    else:
        minutes = (total_seconds // 60) % 60
        hours = (total_seconds // 60) // 60 // 24
        days = (total_seconds // 60) // 60 % 24
        return f"{int(days)}d {int(hours)}h {int(minutes)}m ago"


# Retrieve MOH repo
try:
    mohrepo = git.Repo.clone_from(MOHREPO_URL, mohdir_fp, depth=1)
    latest_mohrepo_commit_datetime = mohrepo.commit().committed_datetime

    # gitpython uses its own tz object, replace it
    latest_mohrepo_commit_datetime = pd.Timestamp(
        latest_mohrepo_commit_datetime
    ).tz_convert("Asia/Kuala_Lumpur")
    time_since_last_mohrepo_commit = (
        pd.Timestamp.now(tz="Asia/Kuala_Lumpur") - latest_mohrepo_commit_datetime
    )
except git.GitCommandError as e:
    print("Failed to clone MOH repo! Thrown exception:")
    print(e)


# Retrieve CITF repo
try:
    citfrepo = git.Repo.clone_from(CITFREPO_URL, citfdir_fp, depth=1)
    latest_citfrepo_commit_datetime = citfrepo.commit().committed_datetime

    # gitpython uses its own tz object, replace it
    latest_citfrepo_commit_datetime = pd.Timestamp(
        latest_citfrepo_commit_datetime
    ).tz_convert("Asia/Kuala_Lumpur")
    time_since_last_citfrepo_commit = (
        pd.Timestamp.now(tz="Asia/Kuala_Lumpur") - latest_citfrepo_commit_datetime
    )
except git.GitCommandError as e:
    print("Failed to clone CITF repo! Thrown exception:")
    print(e)

print(f"{timer() - start_init_timer:5.1f}s: Git clone complete")

## Prepare data -------------------------------

# MOH repo
cases_malaysia = pd.read_csv(
    mohdir_fp / "epidemic/cases_malaysia.csv", index_col=0, parse_dates=[0]
)
cases_state = pd.read_csv(
    mohdir_fp / "epidemic/cases_state.csv", index_col=0, parse_dates=[0]
)
deaths_malaysia = pd.read_csv(
    mohdir_fp / "epidemic/deaths_malaysia.csv", index_col=0, parse_dates=[0]
)
deaths_state = pd.read_csv(
    mohdir_fp / "epidemic/deaths_state.csv", index_col=0, parse_dates=[0]
)
tests_malaysia = pd.read_csv(
    mohdir_fp / "epidemic/tests_malaysia.csv", index_col=0, parse_dates=[0]
)
tests_state = pd.read_csv(
    mohdir_fp / "epidemic/tests_state.csv", index_col=0, parse_dates=[0]
)
hospital_state = pd.read_csv(
    mohdir_fp / "epidemic/hospital.csv", index_col=0, parse_dates=[0]
)
hospital_malaysia = hospital_state.groupby("date").sum()
icu_state = pd.read_csv(mohdir_fp / "epidemic/icu.csv", index_col=0, parse_dates=[0])
icu_malaysia = icu_state.groupby("date").sum()
pkrc_state = pd.read_csv(mohdir_fp / "epidemic/pkrc.csv", index_col=0, parse_dates=[0])
pkrc_malaysia = pkrc_state.groupby("date").sum()

# CITF repo
vaxreg_national = pd.read_csv(
    citfdir_fp / "registration/vaxreg_malaysia.csv", index_col=0, parse_dates=[0]
)
vaxreg_state = pd.read_csv(
    citfdir_fp / "registration/vaxreg_state.csv", index_col=0, parse_dates=[0]
)
vax_national = pd.read_csv(
    citfdir_fp / "vaccination/vax_malaysia.csv", index_col=0, parse_dates=[0]
)
vax_state = pd.read_csv(
    citfdir_fp / "vaccination/vax_state.csv", index_col=0, parse_dates=[0]
)

# Round out the no-clusters column for national cases
cases_malaysia["cluster_none"] = cases_malaysia["cases_new"] - cases_malaysia.drop(
    columns=["cases_new"]
).sum(axis="columns")

# Add a total tests column
tests_malaysia["total_tests"] = tests_malaysia.sum(axis="columns")

## Prepare the API ------------------------------------
class MsianState(str, Enum):
    johor = "johor"
    kedah = "kedah"
    kelantan = "kelantan"
    melaka = "melaka"
    ns = "negerisembilan"
    pahang = "pahang"
    perak = "perak"
    perlis = "perlis"
    penang = "penang"
    sabah = "sabah"
    sarawak = "sarawak"
    selangor = "selangor"
    terengganu = "terengganu"
    kl = "kl"
    labuan = "labuan"
    putrajaya = "putrajaya"
    allstates = "allstates"


pretty_state_name = {
    MsianState.johor: "Johor",
    MsianState.kedah: "Kedah",
    MsianState.kelantan: "Kelantan",
    MsianState.melaka: "Melaka",
    MsianState.ns: "Negeri Sembilan",
    MsianState.pahang: "Pahang",
    MsianState.perak: "Perak",
    MsianState.perlis: "Perlis",
    MsianState.penang: "Pulau Pinang",
    MsianState.sabah: "Sabah",
    MsianState.sarawak: "Sarawak",
    MsianState.selangor: "Selangor",
    MsianState.terengganu: "Terengganu",
    MsianState.kl: "W.P. Kuala Lumpur",
    MsianState.labuan: "W.P. Labuan",
    MsianState.putrajaya: "W.P. Putrajaya",
}

reverse_pretty_state_name = {j: i for i, j in pretty_state_name.items()}

end_init_timer = timer()
print(f"{end_init_timer - start_init_timer:5.1f}s: API init complete")


@app.get("/")
def return_root(
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    state: Optional[MsianState] = None,
):
    """
    Returns key COVID19 epidemic data for Malaysia between the specified
    `start_date` and `end_date`. Use the `detailed/` endpoint for detailed info.

    Args
    ----
    `start_date`: str
    + Start date in ISO format e.g. "2021-01-01"
    + If `start_date` is not specified, defaults to five days before current date in GMT+8

    `end_date`: str
    + End date in ISO format e.g. "2021-01-05"
    + If `end_date` is not specified, defaults to current date in GMT+8

    `state`: str
    + The following values are allowed for `state`:
        "johor", "kedah", "kelantan", "melaka", "negerisembilan", "pahang",
        "perak", "perlis", "penang", "sabah", "sarawak", "selangor",
        "terengganu", "kl", "labuan", "putrajaya", "allstates"

    + If `state` is not specified, returns national level data which includes:
        + count of daily new cases,
        + count of daily deaths,
        + cumulative count of 1st/2nd/total vaccine shots administered,
        + count of daily tests

    + If `state` is specified, returns state level data which includes:
        + count of daily new cases,
        + count of daily deaths,
        + cumulative count of 1st/2nd/total vaccine shots administered,
        + count of daily tests

    + If `state` is specified as "allstates", returns data for all states

    Returns
    -------
    `ans`: JSON response

    Notes
    -----
    + Data source is from the [Malaysian Ministry of Health's github data release]
    (https://github.com/MoH-Malaysia/covid19-public/blob/main/epidemic/README.md)
    + NaNs in the data will be returned as -9999. Some of the data updates on a
    slower cycle, leaving blank entries

    """
    print(f"start_date: {start_date}, end_date: {end_date}, state: {state}")
    if start_date is None:
        start_date: datetime.date = (
            pd.Timestamp.now(tz="Asia/Kuala_Lumpur") - pd.Timedelta("120h")
        ).date()
    if end_date is None:
        end_date: datetime.date = pd.Timestamp.now(tz="Asia/Kuala_Lumpur").date()

    # TODO: Figure out consistent return API for national and state
    # Return national data
    if state is None:
        ans = pd.concat(
            [
                cases_malaysia.loc[start_date:end_date, "cases_new"],
                deaths_malaysia.loc[start_date:end_date, "deaths_new"],
                vax_national.loc[
                    start_date:end_date, ["cumul_partial", "cumul_full", "cumul_full"]
                ],
                tests_malaysia.loc[start_date:end_date, "total_tests"],
            ],
            axis="columns",
        )
        print(vax_national.loc[start_date:end_date])

    elif state == MsianState.allstates:
        ans_list = {}

        # Here is where I wish this was SQL instead
        # TODO: Must be a cleaner way to do this
        cases_state_selected = cases_state.loc[
            start_date:end_date, ["cases_new", "state"]
        ].reset_index(drop=False)
        deaths_state_selected = deaths_state.loc[
            start_date:end_date, ["deaths_new", "state"]
        ].reset_index(drop=False)
        pregrouped_ans = cases_state_selected.merge(
            deaths_state_selected, on=["state", "date"], how="inner"
        )
        vax_state_selected = vax_state.loc[
            start_date:end_date, ["cumul_partial", "cumul_full", "cumul_full", "state"]
        ].reset_index(drop=False)
        pregrouped_ans = pregrouped_ans.merge(
            vax_state_selected, on=["state", "date"], how="inner"
        )

        print(pregrouped_ans.info())

        for statename, ans in pregrouped_ans.groupby("state"):
            # Change pd.DatetimeIndex to datetime.date
            ans = ans.set_index("date")
            ans.index = ans.index.map(lambda x: x.date())

            # Purge NaNs as JSON can't serialize them
            # Rather return an obviously wrong answer than return ambiguous 0
            ans = ans.fillna(value=-9999)

            # Remove the state column
            ans = ans.drop(columns="state")

            # Get all data to be int
            ans = ans.astype(int)

            # Considering split and index
            # Ended up preferring index
            ans = ans.to_dict(orient="index")
            ans_list[reverse_pretty_state_name.get(statename)] = ans

        return ans_list

    else:
        ans = pd.concat(
            [
                cases_state[cases_state["state"] == pretty_state_name.get(state)].loc[
                    start_date:end_date, "cases_new"
                ],
                deaths_state[deaths_state["state"] == pretty_state_name.get(state)].loc[
                    start_date:end_date, "deaths_new"
                ],
                vax_state[vax_state["state"] == pretty_state_name.get(state)].loc[
                    start_date:end_date, ["cumul_partial", "cumul_full", "cumul_full"]
                ],
            ],
            axis="columns",
        )

    # Change pd.DatetimeIndex to datetime.date
    ans.index = ans.index.map(lambda x: x.date())

    # Purge NaNs as JSON can't serialize them
    # Rather return an obviously wrong answer than return ambiguous 0
    ans = ans.fillna(value=-9999)

    # Get all data to be int
    ans = ans.astype(int)

    # Considering split and index
    # Ended up preferring index
    # TODO: Resolve warning:
    # UserWarning: DataFrame columns are not unique, some columns will be omitted.
    ans = ans.to_dict(orient="index")

    return ans


@app.get("/detailed")
def return_detailed(
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
    state: Optional[MsianState] = None,
):
    """
    Returns detailed COVID19 epidemic data for Malaysia between the specified
    `start_date` and `end_date`. Use the `/` endpoint for key info only.
    
    Note that detailed info is subject to constant upstream changes from the
    MoH and CITF repos.

    Args
    ----
    `start_date`: str
    + Start date in ISO format e.g. "2021-01-01"
    + If `start_date` is not specified, defaults to five days before current date in GMT+8

    `end_date`: str
    + End date in ISO format e.g. "2021-01-05"
    + If `end_date` is not specified, defaults to current date in GMT+8

    `state`: str
    + The following values are allowed for `state`:
        "johor", "kedah", "kelantan", "melaka", "negerisembilan", "pahang",
        "perak", "perlis", "penang", "sabah", "sarawak", "selangor",
        "terengganu", "kl", "labuan", "putrajaya", "allstates"

    + If `state` is not specified, returns national level data which includes:
        + count of daily new cases,
        + count of daily deaths,
        + cumulative count of 1st/2nd/total vaccine shots administered,
        + count of daily tests
        + (detailed only) 

    + If `state` is specified, returns state level data which includes:
        + count of daily new cases,
        + count of daily deaths,
        + cumulative count of 1st/2nd/total vaccine shots administered,
        + count of daily tests
        + (detailed only)

    + If `state` is specified as "allstates", returns data for all states

    Returns
    -------
    `ans`: JSON response

    Notes
    -----
    + Data source is from the [Malaysian Ministry of Health's github data release]
    (https://github.com/MoH-Malaysia/covid19-public/blob/main/epidemic/README.md)
    + NaNs in the data will be returned as -9999. Some of the data updates on a
    slower cycle, leaving blank entries

    """
    print(f"start_date: {start_date}, end_date: {end_date}, state: {state}")
    if start_date is None:
        start_date: datetime.date = (
            pd.Timestamp.now(tz="Asia/Kuala_Lumpur") - pd.Timedelta("120h")
        ).date()
    if end_date is None:
        end_date: datetime.date = pd.Timestamp.now(tz="Asia/Kuala_Lumpur").date()

    # TODO: Figure out consistent return API for national and state
    # Return national data
    if state is None:
        ans = {}

        # Add each set of national data to the response
        ans["cases_malaysia"] = cases_malaysia.loc[start_date:end_date]
        ans["deaths_malaysia"] = deaths_malaysia.loc[start_date:end_date]
        ans["vax_malaysia"] = vax_national.loc[start_date:end_date]
        ans["tests_malaysia"] = tests_malaysia.loc[start_date:end_date]
        ans["hospital_malaysia"] = hospital_malaysia.loc[start_date:end_date]
        ans["icu_malaysia"] = icu_malaysia.loc[start_date:end_date]
        ans["pkrc_malaysia"] = pkrc_malaysia.loc[start_date:end_date]

        # Format each set
        for i in ans.keys():
            formatted_data = ans[i]
            # Change pd.DatetimeIndex to datetime.date
            formatted_data.index = formatted_data.index.map(lambda x: x.date())

            # Purge NaNs as JSON can't serialize them
            # Rather return an obviously wrong answer than return ambiguous 0
            formatted_data = formatted_data.fillna(value=-9999)

            # Get all numeric data to be int, ignoring strings
            formatted_data = formatted_data.astype(int, errors="ignore")

            # Considering split and index
            # Ended up preferring index
            formatted_data = formatted_data.to_dict(orient="index")

            # Assign to response
            ans[i] = formatted_data

        return ans

    elif state == MsianState.allstates:
        ans = {}
        for i, j in pretty_state_name.items():
            ans[i] = return_detailed(start_date=start_date, end_date=end_date, state=i)
        return ans

    else:
        ans = {}

        # Add each set of state data to the response
        ans["cases_state"] = cases_state[
            cases_state["state"] == pretty_state_name.get(state)
        ].loc[start_date:end_date]
        ans["deaths_state"] = deaths_state[
            deaths_state["state"] == pretty_state_name.get(state)
        ].loc[start_date:end_date]
        ans["vax_state"] = vax_state[
            vax_state["state"] == pretty_state_name.get(state)
        ].loc[start_date:end_date]
        ans["tests_state"] = tests_state[
            tests_state["state"] == pretty_state_name.get(state)
        ].loc[start_date:end_date]
        ans["hospital_state"] = hospital_state[
            hospital_state["state"] == pretty_state_name.get(state)
        ].loc[start_date:end_date]
        ans["icu_state"] = icu_state[
            icu_state["state"] == pretty_state_name.get(state)
        ].loc[start_date:end_date]
        ans["pkrc_state"] = pkrc_state[
            pkrc_state["state"] == pretty_state_name.get(state)
        ].loc[start_date:end_date]

        # Format each set
        for i in ans.keys():
            formatted_data = ans[i]

            # Drop the state column
            formatted_data = formatted_data.drop(columns="state")

            # Change pd.DatetimeIndex to datetime.date
            formatted_data.index = formatted_data.index.map(lambda x: x.date())

            # Purge NaNs as JSON can't serialize them
            # Rather return an obviously wrong answer than return ambiguous 0
            formatted_data = formatted_data.fillna(value=-9999)

            # Get all numeric data to be int, ignoring strings
            formatted_data = formatted_data.astype(int, errors="ignore")

            # Considering split and index
            # Ended up preferring index
            formatted_data = formatted_data.to_dict(orient="index")

            # Assign to response
            ans[i] = formatted_data

        return ans


@app.get("/ascii", response_class=PlainTextResponse)
def return_ascii():
    """
    Returns a terminal-friendly printout of latest national stats.
    Equivalent to calling the root API with no parameters. Refer
    to the docstring of the root API for more info.

    Intended usage in terminal:
    ```
    $ curl msiacovidapi.herokuapp.com/ascii

    Latest update - Msia COVID19
    MOH data updated 3h 5m ago
    Vax data updated 8h 49m ago

                cases_new  deaths_new  dose1_cumul  \
    -------------------------------------------------
    2021-08-09     17,236         212   15,959,596
    2021-08-10     19,991         201   16,119,916
    2021-08-11     20,780         211   16,347,422
    2021-08-12     21,668         318   16,545,384
    2021-08-13     21,468         277   16,707,566

                dose2_cumul  total_cumul  total_tests
    -------------------------------------------------
    2021-08-09    9,048,634   25,008,230      153,561
    2021-08-10    9,246,295   25,366,211      144,565
    2021-08-11    9,516,141   25,863,563      169,444
    2021-08-12    9,843,521   26,388,905      171,982
    2021-08-13   10,144,199   26,851,765       -9,999

    ```
    """
    ans = pd.DataFrame.from_dict(return_root(), orient="index")

    # Rename some column names
    ans = ans.rename(
        columns={
            "cases_new": "New cases",
            "deaths_new": "Deaths",
            "cumul_partial": "Sum partially vax'ed",
            "cumul_full": "Sum fully vax'ed",
            "total_tests": "Daily tests",
        }
    )

    # Add space to columns for better spacing
    # Easiest workaround
    ans.columns = [f" {i}" for i in ans.columns]

    ans_string = ans.to_string(
        line_width=60,
        justify="right",  # complements spacing workaround
        # ref: https://stackoverflow.com/a/41447478/13095028
        formatters=[
            lambda x: "{:,}".format(x)
            for _, dtype in ans.dtypes.items()
            if dtype in [np.dtype("int64"), np.dtype("float64")]
        ],
    )

    # Further format the ASCII return
    # Calculate the line width
    lwidth = len(ans_string.split("\n", 1)[0])

    # Add "table line" (what's this called?)
    columnrow, body = ans_string.split("\n", 1)
    ans_string = columnrow + "\n" + "-" * lwidth + "\n" + body

    # Add "table line" for subsequent rows
    # Not proud with how I did this
    pieces = ans_string.split("\n\n")
    ans_string = pieces[0]
    for i in pieces[1:]:
        front_piece, back_piece = i.split("\n", 1)
        ans_string = (
            ans_string + "\n\n" + front_piece + "\n" + "-" * lwidth + "\n" + back_piece
        )

    # Add a header printout
    header = "\nLatest update - Msia COVID19\n"
    # header += f"Source: {MOHREPO_URL}\n\n"
    header += f"MOH data updated {pprint_time(time_since_last_mohrepo_commit.total_seconds())}\n"
    header += f"Vax data updated {pprint_time(time_since_last_citfrepo_commit.total_seconds())}\n\n"
    ans_string = header + ans_string

    # Add a footer
    # footer = f"\nData last updated {pprint_time(time_since_last_mohrepo_commit.total_seconds())}\n\n"
    footer = "\n\n"
    ans_string = ans_string + footer

    return ans_string


@app.get("/ping")  # , response_class=PlainTextResponse)
def return_ping():
    """
    Ping endpoint to check API status
    """
    return {"pong"}
