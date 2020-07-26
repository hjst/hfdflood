# Tools

## csv2json.py

There's [an archive of the real time flood monitoring data](https://environment.data.gov.uk/flood-monitoring/archive), but each file is…
 
 - ~50MB in size
 - includes readings from *every* station
 - is in CSV format instead of JSON

Convert from the CSV daily archive format to our JSON "dayfile" format with:

    python3 csv2json.py MEASURE_ID < readings-2019-12-25.csv > dayfile-2019-12-25.json

The first line of the CSV input must be a header line, to identify the ordering of the fields (this is always the case with files sourced from the API archive).

Note: it doesn't distinguish date ranges, it processes the input line-by-line ignoring non-matching lines; if you feed it a month of concatenated data, you will get a month of data out in one lump. E.g. if you do this…

    cat readings-2019-12-*.csv | python3 csv2json.py MEASURE_ID

…it will not create 31 files for December, it will give you one big JSON object for the whole month on stdout.

### Processing batches of archive files

Usually I'm processing a batch of CSV archive files in one go, which looks like this:

    find path/to/CSVs -type f -name "readings*.csv" -exec bash -c '
    for csvfile do
      basename "$csvfile"
      python3 csv2json.py 055807_TG_320-level-stage-i-15_min-mASD < "$csvfile" > "${csvfile%.csv}.json"
    done' bash {} +

Then rename the JSON files to match a dayfile output by the ingest lambda function (usually what I want) with something like this (assuming a bash-like shell):

    cd path/to/CSVs
    for jsonfile in readings-*.json; do mv -i "$jsonfile" "${jsonfile#readings-}"; done
