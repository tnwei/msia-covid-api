# Malaysia COVID data loader

This repo stores the source code for a rudimentary AWS Chalice app that loads data for COVID19 cases in Malaysia. It reads from [this fantastic Google Doc](https://docs.google.com/spreadsheets/d/15A43eb68LT7gg_k9VavYwS1R2KkCTpvigYMn5KT9RTM/) that contains up-to-date information on the COVID19 pandemic in Malaysia, updated after daily press conferences by the Ministry of Health.

Disclaimer: I am not the owner of the aformentioned Google Doc.

## How to deploy

Would like to share my link, but I would prefer to keep my AWS usage low. Strip the functions from `app.py` for your own use, or deploy this yourself (and potentially learn a new skill :) ):

1. Install AWS Chalice with `pip install chalice`
2. You'll need an AWS account, free tier is more than enough. 
3. Setup your AWS credentials [https://github.com/aws/chalice#credentials](https://github.com/aws/chalice#credentials), 
4. Run `chalice new-project YOUR-PROJECT-NAME-HERE` to initialize, then replace the default `app.py` and `requirements.txt` with those in this repo.
5. Run `chalice deploy` from within the project folder. Deploying will take a while as `pandas` has a few too many dependencies, especially in the context of a serverless application.
6. When done, Chalice will show your Rest API URL.

## Usage

``` python
import pandas as pd
URL="YOUR-AWS-LAMBDA-API"

# Latest reported cases, nationwide
nat = df.read_json(URL + 'latest/national')

# nat.tail()
#             confirmed_cases  fatalities  recovered  active  daily_change
# 2020-04-13             4817          77       2276    2464         134.0
# 2020-04-14             4987          82       2478    2427         170.0
# 2020-04-15             5072          83       2647    2342          85.0
# 2020-04-16             5182          84       2766    2332         110.0
# 2020-04-17             5251          86       2967    2198          69.0

# Latest reported cases, state-by-state
states = df.read_json(URL + 'latest/states')

# states.tail()
#             Perlis  Kedah  Pulau Pinang  Perak  Selangor  ...  Sabah  Sarawak  WP Labuan  WP Kuala Lumpur  WP Putrajaya
# 2020-04-13    17.0   93.0         116.0  247.0      1249  ...  280.0    348.0       15.0            830.0          54.0
# 2020-04-14    18.0   93.0         119.0  250.0      1299  ...  285.0    363.0       15.0            899.0          54.0
# 2020-04-15    18.0   94.0         119.0  250.0      1316  ...  285.0    371.0       15.0            926.0          54.0
# 2020-04-16    18.0   94.0         119.0  251.0      1329  ...  288.0    387.0       15.0            952.0          55.0
# 2020-04-17    18.0   94.0         119.0  252.0      1338  ...  293.0    397.0       16.0            971.0          55.0
```
