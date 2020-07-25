# hfdflood

Notes: https://workflowy.com/#/6578ce38500a

## Environment variables

| Variable | Notes | Example |
| - | - | - |
| `MEASURE_ID` | You can find this in the `measures` array in [the station response](https://environment.data.gov.uk/flood-monitoring/id/stations/055807_TG_320) | `055807_TG_320-level-stage-i-15_min-mASD` |
| `BUCKET` | Name of the S3 bucket | `rawdata.herefordflooded.uk` |
| `LOG_LEVEL` | How verbose do you want the logs? Defaults to `INFO` | `DEBUG`, `INFO` or `WARNING` |