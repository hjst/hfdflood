import os
import logging
from datetime import date, timedelta, datetime
import json
from urllib.request import Request, urlopen
import math
import boto3

s3 = boto3.resource('s3')

BUCKET = os.environ['BUCKET']
MEASURE_ID = os.environ['MEASURE_ID']
INTERVAL = 15  # readings interval in minutes
try:
    LOG_LEVEL = os.environ['LOG_LEVEL']
except KeyError:
    LOG_LEVEL = "INFO"  # default level

logging.basicConfig(format='%(levelname)s: %(message)s')
log = logging.getLogger()
log.setLevel(LOG_LEVEL)


def bootstrap_series(initial_date: date):
    """Bootstrap an empty (or suspended) series of readings, beginning from the given date."""
    log.info(f"Bootstrapping the series, beginning at {initial_date.isoformat()}")
    batched_readings, meta = fetch_readings_since(initial_date.isoformat())
    # Append all readings received to their respective day's JSON file in the `items` array
    for day, readings in batched_readings.items():
        add_to_dayfile(day, readings, meta)


def find_most_recent_dayfile(day, tries=0, search_limit=7):
    """Return the date of the most recent dayfile, searching backwards in time for day, day-1, day-2 etc.."""
    log.info(f"Entering find_most_recent_dayfile(day={day.isoformat()}, tries={tries})")
    try:
        s3object = s3.Object(BUCKET, format_dayfile_filename(day))
        s3object.get()
        log.info(f"Success, found dayfile {format_dayfile_filename(day)}")
        return day
    except s3.meta.client.exceptions.NoSuchKey:
        if tries == search_limit:
            log.warning(f"Could not find a recent dayfile. Searched {search_limit} days into the past."
                        f" Returning oldest date: {day.isoformat()}")
            return day
        else:
            log.info(f"Caught s3.meta.client.exceptions.NoSuchKey exception")
            return find_most_recent_dayfile(day - timedelta(days=1), tries + 1)


def format_dayfile_filename(day: date):
    """Return the given day as a dayfile filename string."""
    return f"{day.isoformat()}.json"


def str_to_datetime(datetime_string: str):
    """Return a datetime object created from a string in the format received from the EA flood API."""
    if datetime_string[-1:] == "Z":
        # The datetime string returned by the API has a "Z" at the end, which chokes python
        datetime_string = datetime_string[:-1]
    try:
        datetime_object = datetime.fromisoformat(datetime_string)
    except ValueError:
        log.error("The format of the dateTime field returned by the API is not what we expected")
        raise
    return datetime_object


def trim_reading(reading):
    """Return a minimal subset of a given reading from the API, discarding the fields we don't need."""
    # Note: the measure field is redundant and the URL in the id field will 404 after a few days
    log.debug(f"Reading: {reading['dateTime']}, value: {reading['value']}")
    try:
        return {key: reading[key] for key in ('dateTime', 'value')}
    except KeyError:
        log.error(f"One of the vital fields is missing from this reading: {reading}")
        raise


def num_of_readings(since: datetime, until: datetime = datetime.now()):
    """"Return the estimated number of readings that would exist between two points in time."""
    delta = until - since
    # We use floor() to round down because 1.99999 readings is 1 reading in an interval, not 2
    return math.floor((delta.total_seconds() / 60) / INTERVAL)


def fetch_readings_since(since):
    """Return a list of all the readings available from the given datetime until now."""

    query_url = f"https://environment.data.gov.uk/flood-monitoring" \
                f"/id/measures/{MEASURE_ID}/readings?since={since}"
    estimate = num_of_readings(str_to_datetime(since))
    if estimate > 500:
        # If we're asking for more than the default limit (500) add the _limit param,
        # otherwise omit it to improve our chances of a cache hit
        log.warning(f"Eek! We're asking for a lot of readings: estimate={estimate}")
        query_url += f"&_limit={estimate + 1}"  # +1 for luck
    log.debug(f"Requesting URL: {query_url}")
    # TODO: wrap this request in try/except once I see some real-world errors
    # TODO: add support for Last-Modified headers and If-Modified-Since requests
    # TODO: "At times of high load or in future versions of this API the service may redirect to an alternative URL."
    # TODO: bump the bot version to 1.0
    req = Request(query_url, headers={'User-Agent': 'HerefordFloodBot/0.1 (+https://bot.herefordflooded.uk)'})
    res = urlopen(req)
    res_body = res.read()
    encoding = res.info().get_content_charset(failobj='utf-8')
    parsed_response = json.loads(res_body.decode(encoding))
    orig_readings = sorted(parsed_response['items'], key=lambda k: k['dateTime'])
    log.info(f"API returned {len(orig_readings)} new readings since {since}")
    readings = dict()
    for reading in orig_readings:
        day_of_reading = str_to_datetime(reading['dateTime']).date().isoformat()
        try:
            readings[day_of_reading].append(trim_reading(reading))
        except KeyError:
            readings[day_of_reading] = [trim_reading(reading)]

    return readings, parsed_response['meta']


def add_to_dayfile(day, readings, meta):
    """Write the given readings into the dayfile for the given day. Handle creating and updating files."""
    filename = format_dayfile_filename(datetime.fromisoformat(day).date())
    s3object = s3.Object(BUCKET, filename)
    try:
        dayfile = json.loads(s3object.get()['Body'].read().decode('utf-8'))
        log.debug(f"Reading existing dayfile {filename}, found {len(dayfile['items'])} existing reading/s")
        dayfile['items'] += readings
        # Update existing dayfile
        s3object.put(Body=(bytes(json.dumps(dayfile, indent=2).encode('UTF-8'))))
        log.info(f"Updated existing dayfile {filename}, added {len(readings)} new reading/s")

    except s3.meta.client.exceptions.NoSuchKey:
        # Create a new dayfile
        # TODO: remove indentation/pretty-printing the JSON, it's not necessary
        s3object.put(Body=(bytes(json.dumps({'meta': meta, 'items': readings}, indent=2).encode('UTF-8'))))
        log.info(f"Created a new dayfile {filename} with {len(readings)} reading/s")


def lambda_handler(event, context):
    # Try to find the most recent dayfile (trying today, today-1, today-2 etc.)
    dayfile_date = find_most_recent_dayfile(date.today())
    dayfile_filename = format_dayfile_filename(dayfile_date)
    dayfile = {}

    try:
        log.info(f"Opening most recent dayfile: {dayfile_filename}")
        s3object = s3.Object(BUCKET, dayfile_filename)
        dayfile = json.loads(s3object.get()['Body'].read().decode('utf-8'))
    except s3.meta.client.exceptions.NoSuchKey:
        # The dayfile doesn't exist, probably because this is the first time we're being run
        log.warning(f"Could not open dayfile: {dayfile_filename}; Entering bootstrap mode")
        bootstrap_series(dayfile_date)
        return None  # exit early in a Lambda-friendly way

    # find the last known reading from the items array
    last_known_reading = sorted(dayfile['items'], key=lambda k: k['dateTime'], reverse=True)[0]['dateTime']
    log.info(f"Found last known reading: {last_known_reading}")

    # Request readings taken since that last reading from the API
    batched_readings, meta = fetch_readings_since(last_known_reading)

    # Append all readings received to their respective day's JSON file in the `items` array
    for day, readings in batched_readings.items():
        add_to_dayfile(day, readings, meta)
