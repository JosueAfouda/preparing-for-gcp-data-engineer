import time
import gzip
import logging
import argparse
import datetime
from google.cloud import pubsub_v1
from google.pubsub_v1.types import GetTopicRequest

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TOPIC = 'sandiego'
INPUT = 'sensor_obs2008.csv.gz'

def publish(publisher, topic_path, events):
    numobs = len(events)
    if numobs > 0:
        logging.info(f'Publishing {numobs} events from {get_timestamp(events[0])}')
        for event_data in events:
            publisher.publish(topic_path, event_data)

def get_timestamp(line):
    line = line.decode('utf-8')  # convert from bytes to str
    timestamp = line.split(',')[0]
    return datetime.datetime.strptime(timestamp, TIME_FORMAT)

def simulate(topic_path, ifp, firstObsTime, programStart, speedFactor, publisher):
    def compute_sleep_secs(obs_time):
        time_elapsed = (datetime.datetime.utcnow() - programStart).seconds
        sim_time_elapsed = ((obs_time - firstObsTime).days * 86400.0 +
                            (obs_time - firstObsTime).seconds) / speedFactor
        return sim_time_elapsed - time_elapsed

    topublish = []

    for line in ifp:
        event_data = line
        obs_time = get_timestamp(line)

        if compute_sleep_secs(obs_time) > 1:
            publish(publisher, topic_path, topublish)
            topublish = []

            to_sleep_secs = compute_sleep_secs(obs_time)
            if to_sleep_secs > 0:
                logging.info(f'Sleeping {to_sleep_secs} seconds')
                time.sleep(to_sleep_secs)

        topublish.append(event_data)

    publish(publisher, topic_path, topublish)

def peek_timestamp(ifp):
    pos = ifp.tell()
    line = ifp.readline()
    ifp.seek(pos)
    return get_timestamp(line)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send sensor data to Cloud Pub/Sub in small groups, simulating real-time behavior')
    parser.add_argument('--speedFactor', help='Example: 60 implies 1 hour of data sent to Cloud Pub/Sub in 1 minute', required=True, type=float)
    parser.add_argument('--project', help='Example: --project $PROJECT_ID', required=True)
    args = parser.parse_args()

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    # Initialise le client Pub/Sub
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(args.project, TOPIC)

    # Vérifie si le topic existe, sinon le crée
    try:
        publisher.get_topic(request=GetTopicRequest(topic=topic_path))
        logging.info(f'Reusing Pub/Sub topic {TOPIC}')
    except Exception:
        publisher.create_topic(request={"name": topic_path})
        logging.info(f'Creating Pub/Sub topic {TOPIC}')

    # Lit et simule l'envoi des données
    programStartTime = datetime.datetime.utcnow()
    with gzip.open(INPUT, 'rb') as ifp:
        header = ifp.readline()
        firstObsTime = peek_timestamp(ifp)
        logging.info(f'Sending sensor data from {firstObsTime}')
        simulate(topic_path, ifp, firstObsTime, programStartTime, args.speedFactor, publisher)
