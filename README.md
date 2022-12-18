# msia-covid-api

![LGTM Grade](https://img.shields.io/lgtm/grade/python/github/tnwei/msia-covid-api)
![License](https://img.shields.io/github/license/tnwei/msia-covid-api)

Query `https://msia-covid-api-371415.uc.r.appspot.com` for API access to [case count, testing, contact tracing](https://github.com/MoH-Malaysia/covid19-public), [and vaccination](https://github.com/CITF-Malaysia/citf-public) data, released and updated by the Malaysian Ministry of Health. 
Design decisions documented in [ARCHITECTURE.md](ARCHITECTURE.md).

## Usage

Call the `/` endpoint for summary info. Returns new cases, deaths, cumulative vaccinations and tests. Example query: `https://msia-covid-api-371415.uc.r.appspot.com/?start_date=2021-08-08&end_date=2021-08-10&state=kl`

Call the `detailed/` endpoint using the same params above to retrieve detailed statistics uploaded by MoH. Example query: `https://msia-covid-api-371415.uc.r.appspot.com/detailed/?start_date=2021-08-08&end_date=2021-08-10&state=kl`

Refer to API docs for more info: `https://msia-covid-api-371415.uc.r.appspot.com/docs`

Use the following param for both the summary and detailed endpoints:

+ `start_date`: YYYY-MM-DD format e.g. 2021-08-09. If left blank, defaults to five days before current date.
+ `end_date`: YYYY-MM-DD format e.g. 2021-08-13. If left blank, defaults to current date.
+ `state`: Leave blank for national data, specify `allstates` for all states, specify specific state names (ref to docs) for state data.


## Example usage for data analysis in Python

``` python
import requests
import pandas as pd

url = "https://msia-covid-api-371415.uc.r.appspot.com/"

# National summary for last 5 days
nat_sum = requests.get(url).json()
nat_sum_df = pd.DataFrame.from_dict(nat_sum, orient="index")

# State summary for last 5 days
selangor_sum = requests.get(url + "?state=selangor").json()
selangor_sum_df = pd.DataFrame.from_dict(selangor_sum, orient="index")

# Summary of all states for last 5 days
allstates_sum = requests.get(url + "?state=allstates").json()
# allstates returns a Dict of states
selangor_sum_df_from_allstates = pd.DataFrame.from_dict(allstates_sum["selangor"], orient="index")

# National detailed for last 5 days
nat_detailed = requests.get(url + "detailed").json()
print(nat_detailed.keys())
# dict_keys(['cases_malaysia', 'deaths_malaysia', 'vax_malaysia', 'tests_malaysia', 'hospital_malaysia', 'icu_malaysia', 'pkrc_malaysia'])
cases_malaysia = nat_detailed["cases_malaysia"]

# State detailed for last 5 days
selangor_detailed = requests.get(url + "detailed?state=selangor").json()
print(selangor_detailed.keys())
# dict_keys(['cases_state', 'deaths_state', 'vax_state', 'tests_state', 'hospital_state', 'icu_state', 'pkrc_state'])
selangor_cases_state = pd.DataFrame.from_dict(selangor_detailed["cases_state"], orient="index")

# Detailed info of all states for last 5 days
allstates_detailed = requests.get(url + "detailed?state=allstates").json()
print(allstates_detailed.keys())
# dict_keys(['johor', 'kedah', 'kelantan', 'melaka', 'negerisembilan', 'pahang', 'perak', 'perlis', 'penang', 'sabah', 'sarawak', 'selangor', 'terengganu', 'kl', 'labuan', 'putrajaya'])
selangor_cases_state_from_allstates = pd.DataFrame.from_dict(allstates_detailed["selangor"]["cases_state"], orient="index")
```


## cURL from terminal

```
$ curl https://msia-covid-api-371415.uc.r.appspot.com/ascii

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

## Data schema changes

The data schema in source repos are updated as new information is collected and reported, which can lead to the API breaking. For this purpose, changes to the data schema are tracked regularly for in these gists: [case statistics](https://gist.github.com/tnwei/507f582644b9a8c8be167637cea1e2fc) and [vaccination statistics](https://gist.github.com/tnwei/6b1e974ff0fa5463933c94964a831dd0). `generate-data-schema-changelog.py` is used to keep track of data schema updates. Example output: 

``` bash
$ python generate-data-schema-changelog.py citf
$ tail citf-schema-changes.txt -n 18 
Changes in commit b222fd on (2021-08-18 01:07:06+08:00)
-------------------------------------------------------
+vax_malaysia.csv: pending
+vax_state.csv: pending

-vax_malaysia.csv: cansino
-vax_malaysia.csv: pending1
-vax_malaysia.csv: pending2
-vax_state.csv: cansino
-vax_state.csv: pending1
-vax_state.csv: pending2

Changes in commit 536c89 on (2021-08-28 04:35:57+08:00)
-------------------------------------------------------
+vax_malaysia.csv: cansino
+vax_state.csv: cansino
```

## Changes

+ (8ac732a) Migrated to GCP following Heroku free tier shutting down. I plan to keep this online as long as MoH keeps uploading data.

## License

Code is released under the MIT license. For data, quoting the license from the source data repos:

> The data shared in this repository may be used per the terms of reference found in Appendix B of the Pekeliling Pelaksanaan Data Terbuka Bil.1/2015, accessible here:
> https://www.data.gov.my/p/pekeliling-data-terbuka


