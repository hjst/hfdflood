import csv
import json
import sys
import argparse
import datetime

parser = argparse.ArgumentParser(description='Convert flood archive CSV data to JSON "dayfile" format.',
                                 epilog='Reads CSV input on stdin and writes JSON to stdout.')
parser.add_argument('measure', metavar='MEASURE', type=str, nargs=1,
                    help='the measure id whose readings you want to include in the conversion')
args = parser.parse_args()
measure_id = args.measure[0]

hits = list()
headers = list()
line_counter = 0
reader = csv.reader(sys.stdin)

for row in reader:
    if line_counter == 0:
        headers = row
    line_counter += 1
    if any(measure_id in field for field in row):
        hits.append(row)

output_obj = {
    'meta': {
        'hfdflood': {
            'generator': 'csv2json.py',
            'created_at': datetime.datetime.now().isoformat(),
            'version': 1.0,
            'measure_id': measure_id,
            'csv_source': 'https://environment.data.gov.uk/flood-monitoring/archive'
        }
    },
    'items': []
}

hits = sorted(hits)
for reading in hits:
    output_obj['items'].append({
        'dateTime': reading[headers.index('dateTime')],
        'value': float(reading[headers.index('value')])
    })

print(json.dumps(output_obj), file=sys.stdout)
print(f"Hits: {len(hits)}, Lines: {line_counter}, Headers: {headers}", file=sys.stderr)
