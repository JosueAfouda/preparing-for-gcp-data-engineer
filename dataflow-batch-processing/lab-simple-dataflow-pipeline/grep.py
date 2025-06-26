import apache_beam as beam
import sys

def my_grep(line, term):
    if term in line:
        yield line

if __name__ == '__main__':
    input_file = 'sample.csv'
    output_prefix = 'output_csv'
    search_term = 'Paris'  # à adapter selon ce que tu cherches

    p = beam.Pipeline(argv=sys.argv)

    (
        p
        | 'Read CSV' >> beam.io.ReadFromText(input_file, skip_header_lines=1)
        | 'Filter lines' >> beam.FlatMap(lambda line: my_grep(line, search_term))
        | 'Write results' >> beam.io.WriteToText(output_prefix)
    )

    p.run().wait_until_finish()
