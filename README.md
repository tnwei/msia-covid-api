# msia-covid-api

Query `http://msiacovidapi.herokuapp.com/` for API access to [case count, testing, contact tracing](https://github.com/MoH-Malaysia/covid19-public), [and vaccination](https://github.com/CITF-Malaysia/citf-public) data, released and updated by the Malaysian Ministry of Health. 
Note: Work in progress, API subject to further changes until stable (soon). 

## Usage

Example: `https://msiacovidapi.herokuapp.com/?start_date=2021-08-08&end_date=2021-08-10&state=kl`

Params:
+ `start_date`: YYYY-MM-DD format e.g. 2021-08-09
+ `end_date`: YYYY-MM-DD format e.g. 2021-08-13
+ `state`: Leave blank for national data, specify `allstates` for all states, specify specific state names (ref to docs) for state data.

API reference docs: `http://msiacovidapi.herokuapp.com/docs`

## cURL from terminal

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

## License

Code is released under the MIT license. For data, quoting the license from the source data repos:

> The data shared in this repository may be used per the terms of reference found in Appendix B of the Pekeliling Pelaksanaan Data Terbuka Bil.1/2015, accessible here:
> https://www.data.gov.my/p/pekeliling-data-terbuka


