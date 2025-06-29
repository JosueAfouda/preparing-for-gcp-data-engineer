import argparse
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from apache_beam.transforms.window import SlidingWindows
from apache_beam.io.gcp.pubsub import ReadFromPubSub
from apache_beam.io.gcp.bigquery import WriteToBigQuery, BigQueryDisposition
import json
from datetime import datetime

def parse_message(element):
    # Ici tu décodes le message JSON et tu formates ce que tu veux
    record = json.loads(element)
    key = f"{record['sensorId']}"
    speed = float(record['speed'])
    return (key, speed)

def to_bq_row(element):
    key, avg_speed = element
    # Exemple de clé : sensorId_direction_lane
    parts = key.split('_')
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'latitude': float(parts[0]),  # À ajuster selon ton vrai message
        'longitude': float(parts[1]),
        'highway': parts[2],
        'direction': parts[3],
        'lane': int(parts[4]),
        'speed': avg_speed,
        'sensorId': key
    }

def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_topic', required=True)
    parser.add_argument('--output_table', required=True)
    parser.add_argument('--averaging_interval', type=float, default=60.0)
    parser.add_argument('--speedup_factor', type=float, default=60.0)
    args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(StandardOptions).streaming = True

    p = beam.Pipeline(options=pipeline_options)

    averaging_interval = (60 * args.averaging_interval) / args.speedup_factor
    frequency = averaging_interval / 2

    (
        p
        | 'Read PubSub' >> ReadFromPubSub(topic=args.input_topic).with_output_types(bytes)
        | 'Decode' >> beam.Map(lambda x: x.decode('utf-8'))
        | 'Parse' >> beam.Map(parse_message)
        | 'Window' >> beam.WindowInto(SlidingWindows(averaging_interval, frequency))
        | 'Avg per key' >> beam.CombinePerKey(beam.combiners.MeanCombineFn())
        | 'To BQ Row' >> beam.Map(to_bq_row)
        | 'Write BQ' >> WriteToBigQuery(
            args.output_table,
            schema='timestamp:TIMESTAMP,latitude:FLOAT,longitude:FLOAT,highway:STRING,direction:STRING,lane:INTEGER,speed:FLOAT,sensorId:STRING',
            write_disposition=BigQueryDisposition.WRITE_APPEND,
            create_disposition=BigQueryDisposition.CREATE_IF_NEEDED
        )
    )

    p.run()

if __name__ == '__main__':
    import sys
    run(sys.argv[1:])
