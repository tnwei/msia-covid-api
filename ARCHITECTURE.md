# Architecture

## Motivation and design goals

Few months after the Malaysian MoH started releasing COVID data to the public, there has been a number of API projects on github. Despite that, I wasn't able to find one that progressed to hosting a live API for consumption. Thus this project came to be. 

The design goal is to establish a simple and consistent interface to retrieve Malaysian COVID19 stats. The API achieves this by only requiring three inputs from the user: start date, end date, and state. A summary endpoint (`/`) provides only key numbers, while a detailed endpoint (`detailed/`) provides detailed statistics as uploaded by MoH,  with the schema subject to change based on latest updates. Also took this opportunity to build a terminal-friendly interface (the `ascii/` endpoint) for my own usage.

Also, free services only.

## Tooling

For hosting, Heroku was chosen over other alternatives for ease of use. The API will need to undergo a cold start if not accessed within 30 minutes, but that's acceptable since not expecting significant traffic.

FastAPI was chosen as the framework, as it is simple to work with for local development (compared to serverless functions), and provides nice Swagger API docs out of the box. Plus, the typing system is a joy to work with.

## Design

Upon initialization, the application clones the data repos to disk, then serves a HTTP API. The git repos are cloned to temporary directories, allowing the API to run on stateless Heroku Dynos instead of requiring a mounted disk.

An alternative to cloning the data repos would be to set up a RDBMS database. This would be more tedious to set up as the source data is supplied in the form of flat files. As the data repos are updated, figuring out the diffs and updating the database correctly would be a hassle, especially when the source data schema changes (more on this later). By contrast, cloning the repos on startup is a much simpler approach that gets the job done.

Oct 5 update: recently MoH started incorporating individual case data to the repos, ballooning download size from ~4MB to ~80MB. This has slowed down the API coldstart time significantly to a range of 15s to 20s. Explored options, eventually settled on [this tool](https://github.com/romainbutteaud/Kaffeine) instead to keep the free app running.

## Data schema changes

Data schema changes periodically as new information becomes relevant. Example: commit `a6ccca9` in the [CITF repo](https://github.com/CITF-Malaysia/citf-public/) renamed columns for `dose1` and `dose2` to `daily_partial` and `daily_full`, to incorporate the rollout of single-dose vaccines.

The `detailed/` endpoint has no issues with schema changes as it returns available info verbatim. The `/` endpoint explicitly refers to specific column names, and thus is prone to breaking if the columns are changed. Ended up writing `generate-data-schema-changelog.py` to keep track of data schema changes. 
