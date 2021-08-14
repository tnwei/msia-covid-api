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
import git

# Constants
MOHREPO_URL = "https://github.com/MoH-Malaysia/covid19-public"
CITFREPO_URL = "https://github.com/CITF-Malaysia/citf-public"

app = FastAPI()

## Retrieve data to memory -------------------------------

# Setup temp dirs
# Cleans up nicely when FastAPI restarts or shuts down
mohdirobj = tempfile.TemporaryDirectory()
mohdir_fp = Path(mohdirobj.name)
# citfdirobj = tempfile.TemporaryDirectory()
# citfdir_fp = Path(citfdirobj.name)

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


# Clone to tempdirs
try:
    mohrepo = git.Repo.clone_from(MOHREPO_URL, mohdir_fp, depth=1)
    latest_commit_datetime = mohrepo.commit().committed_datetime

    # gitpython uses its own tz object, replace it
    latest_commit_datetime = pd.Timestamp(latest_commit_datetime).tz_convert(
        "Asia/Kuala_Lumpur"
    )
    time_since_last_commit = (
        pd.Timestamp.now(tz="Asia/Kuala_Lumpur") - latest_commit_datetime
    )


except git.GitCommandError as e:
    print("Failed to clone! Thrown exception:")
    print(e)
print(f"{timer() - start_init_timer:5.1f}s: Git clone complete")

# Load data
cases_national = pd.read_csv(
    mohdir_fp / "epidemic/cases_malaysia.csv", index_col=0, parse_dates=[0]
)
cases_state = pd.read_csv(
    mohdir_fp / "epidemic/cases_state.csv", index_col=0, parse_dates=[0]
)
deaths_national = pd.read_csv(
    mohdir_fp / "epidemic/deaths_malaysia.csv", index_col=0, parse_dates=[0]
)
deaths_state = pd.read_csv(
    mohdir_fp / "epidemic/deaths_state.csv", index_col=0, parse_dates=[0]
)
tests = pd.read_csv(
    mohdir_fp / "epidemic/tests_malaysia.csv", index_col=0, parse_dates=[0]
)

# Round out the no-clusters column for national cases
cases_national["cluster_none"] = cases_national["cases_new"] - cases_national.drop(
    columns=["cases_new"]
).sum(axis="columns")

# Add a total tests column
tests["total_tests"] = tests.sum(axis="columns")

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
    Returns COVID19 epidemic data for Malaysia between the specified `start_date`
    and `end_date`.

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
        + count of new cases,
        + count of deaths, and
        + tests over time

    + If `state` is specified, returns state level data which includes:
        + count of new cases,
        + count of deaths

    + If `state` is specified as "allstates", returns data for all states

    Returns
    -------
    `ans`: JSON response

    Notes
    -----
    + Data source is from the [Malaysian Ministry of Health's github data release]
    (https://github.com/MoH-Malaysia/covid19-public/blob/main/epidemic/README.md)
    + NaNs in the data will be returned as -9999

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
                cases_national.loc[start_date:end_date, "cases_new"],
                deaths_national.loc[start_date:end_date, "deaths_new"],
                tests.loc[start_date:end_date, "total_tests"],
            ],
            axis="columns",
        )

    elif state == MsianState.allstates:
        ans_list = {}

        cases_state_selected = cases_state.loc[
            start_date:end_date, ["cases_new", "state"]
        ].reset_index(drop=False)
        deaths_state_selected = deaths_state.loc[
            start_date:end_date, ["deaths_new", "state"]
        ].reset_index(drop=False)
        pregrouped_ans = cases_state_selected.merge(
            deaths_state_selected, on=["state", "date"], how="inner"
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
    ans = ans.to_dict(orient="index")

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
    Source: https://github.com/MoH-Malaysia/covid19-public

                cases_new  deaths_new  total_tests
    ----------------------------------------------
    2021-08-09      17236         212       153561
    2021-08-10      19991         201       144565
    2021-08-11      20780         211       169444
    2021-08-12      21668         318       171982
    2021-08-13      21468         277        -9999
    Data last updated 12h 11m ago
    ```
    """
    ans = pd.DataFrame.from_dict(return_root(), orient="index")
    ans_string = ans.to_string()

    # Further format the ASCII return
    # Calculate the line width
    lwidth = len(ans_string.split("\n", 1)[0])

    # Add table line (what's this called?)
    columnrow, body = ans_string.split("\n", 1)
    ans_string = columnrow + "\n" + "-" * lwidth + "\n" + body

    # Add a header printout
    header = "\nLatest update - Msia COVID19\n"
    header += f"Source: {MOHREPO_URL}\n\n"
    ans_string = header + ans_string

    # Add a footer
    footer = (
        f"\nData last updated {pprint_time(time_since_last_commit.total_seconds())}\n\n"
    )
    ans_string = ans_string + footer

    return ans_string
