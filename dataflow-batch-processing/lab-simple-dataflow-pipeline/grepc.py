import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

def my_grep(line, term):
    if term in line:
        yield line

PROJECT_ID = 'preparing-for-gcp-de'
BUCKET = 'preparing-for-gcp-de'
REGION = 'us-central1'

def run():
    argv = [
        f'--project={PROJECT_ID}',
        '--job_name=dataflow-grep-csv',
        '--save_main_session',
        f'--staging_location=gs://{BUCKET}/staging/',
        f'--temp_location=gs://{BUCKET}/temp/',
        f'--region={REGION}',
        '--worker_machine_type=e2-standard-2',
        '--runner=DataflowRunner',
    ]

    options = PipelineOptions(argv)
    p = beam.Pipeline(options=options)

    input_file = f'gs://{BUCKET}/input/sample.csv'
    output_prefix = f'gs://{BUCKET}/output/filtered_lines'
    search_term = 'Paris'

    (p
     | 'ReadCSV' >> beam.io.ReadFromText(input_file, skip_header_lines=1)
     | 'FilterLines' >> beam.Filter(lambda line: search_term in line)
     | 'WriteOutput' >> beam.io.WriteToText(output_prefix, file_name_suffix='.txt')
    )

    p.run().wait_until_finish()

if __name__ == '__main__':
    run()
