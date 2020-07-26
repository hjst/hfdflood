# hfdflood

Notes: https://workflowy.com/#/6578ce38500a

## Environment variables

| Variable | Notes | Example |
| - | - | - |
| `MEASURE_ID` | You can find this in the `measures` array in [the station response](https://environment.data.gov.uk/flood-monitoring/id/stations/055807_TG_320) | `055807_TG_320-level-stage-i-15_min-mASD` |
| `BUCKET` | Name of the S3 bucket | `dev.rawdata.herefordflooded.uk` |
| `LOG_LEVEL` | How verbose do you want the logs? Defaults to `INFO` | `DEBUG`, `INFO` or `WARNING` |

## Developing locally

You will need…

1. Python 3.7+ available (e.g. `python3 --version`)
2. [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) installed somewhere local (it's available automatically in the Lambda containers)
3. AWS config & credentials set in `~/.aws` ([see docs](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration)); if you can do `aws s3 ls` you're probably fine
4. Environment variables set for the bucket name, measurement id etc. (see above)

You should then be able to run `python3 local-ingest.py` (you may wish to use a separate bucket for dev/testing).