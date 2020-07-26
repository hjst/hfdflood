# Lambda functions for data ingestion & processing

## hfdflood_ingest.py

- Runs on an every-15-minute EventBridge timer
- Maintains a collection of JSON "dayfiles" in an S3 bucket containing the river level readings from a given measure
    + Requests only new readings since the last recorded reading in the current dayfile
    + Can be paused (or fail…) and then "catch up" later (up to ~30 days)
    + Bootstraps itself from an empty bucket, so setting up parallel jobs to track other measures is quick
- Trims extraneous data from the readings in the API response
    + The responses contain useful fields like IDs and URIs which are redundant and temporary respectively
- Sends the number of readings its processing to CloudWatch metrics for monitoring & alerts 

### Environment variables

| Variable | Notes | Example |
| - | - | - |
| `MEASURE_ID` | You can find this in the `measures` array in [the station response](https://environment.data.gov.uk/flood-monitoring/id/stations/055807_TG_320) | `055807_TG_320-level-stage-i-15_min-mASD` |
| `BUCKET` | Name of the S3 bucket | `dev.rawdata.herefordflooded.uk` |
| `LOG_LEVEL` | How verbose do you want the logs? Defaults to `INFO` | `DEBUG`, `INFO` or `WARNING` |

### Developing locally

You will need…

1. Python 3.7+ available (e.g. `python3 --version`)
2. [boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) installed somewhere local (it's available automatically in the Lambda containers)
3. AWS config & credentials set in `~/.aws` ([see docs](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html#configuration)); if you can do `aws s3 ls` you're probably fine
4. Environment variables set for the bucket name, measurement id etc. (see above)

You should then be able to run `python3 local-ingest.py` (you may wish to use a separate bucket for dev/testing).