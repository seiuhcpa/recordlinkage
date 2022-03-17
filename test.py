import os
import csv
import re
import logging
import optparse
import pandas as pd

import dedupe
from unidecode import unidecode


def preProcess(column):
    column = unidecode(column)
    column = re.sub('  +', ' ', column)
    column = re.sub('\n', ' ', column)
    column = column.strip().strip('"').strip("'").lower().strip()
    if not column:
        column = None
    return column


def readData(filename):
    data_d = {}
    with open(filename) as f:
        reader = csv.DictReader(f, )
        for row in reader:
            clean_row = [(k.replace('\ufeff', ''), preProcess(v)) for (k, v) in row.items()]
            row_id = dict(clean_row)['Id']
            data_d[row_id] = dict(clean_row)

    return data_d


def df_to_records(df):
    df.Id = df.Id.astype(str)
    # TODO HAVE BETTER NAME CLEANING
    df['FIRST'] = df['FIRST'].apply(lambda x: preProcess(x))
    df['LAST'] = df['LAST'].apply(lambda x: preProcess(x))
    # TODO replace with "None"
    df.fillna('', inplace=True)
    records = df.set_index('Id').to_dict(orient='index')
    #df = df.set_index('Id')
    #records = df.apply(lambda x: x.dropna().to_dict(), axis=1).to_dict()
    return records


if __name__ == '__main__':
    optp = optparse.OptionParser()
    optp.add_option('-v', '--verbose', dest='verbose', action='count',
                    help='Increase verbosity (specify multiple times for more)'
                    )
    (opts, args) = optp.parse_args()
    log_level = logging.WARNING
    if opts.verbose:
        if opts.verbose == 1:
            log_level = logging.INFO
        elif opts.verbose >= 2:
            log_level = logging.DEBUG

    logging.getLogger().setLevel(log_level)
    input_file = 'sample_data.csv'
    output_file = 'csv_example_output.csv'
    settings_file = 'data_matching_learned_settings'
    training_file = 'data_matching_training.json'

    print('importing data ...')
    # data_d = read_data(input_file)
    df = pd.read_csv(input_file)
    df_a = df[df.GROUP == 1]
    df_b = df[df.GROUP == 2]
    data_1 = df_to_records(df_a)
    data_2 = df_to_records(df_b)

    print("test")

    if os.path.exists(settings_file):
        print('reading from', settings_file)
        with open(settings_file, 'rb') as sf:
            linker = dedupe.StaticRecordLink(sf)
    else:
        # TODO CREATE SYSTEM FOR AUTOMATIC MATCHES? LIKE ON HCPA ID? ADD TO TRAINING ALGO?
        fields = [
            {'field': 'CHAPTER', 'type': 'Exact'},
            {'field': 'FIRST', 'type': 'String'},
            {'field': 'LAST', 'type': 'String'},
            {'field': 'BIRTHDATE', 'type': 'DateTime', 'has missing': True},
            {'field': 'HIREDATE', 'type': 'DateTime', 'has missing': True},
            #{'field': 'SHIFT', 'type': 'String', 'has missing': True},
        ]
        linker = dedupe.RecordLink(fields)

        if os.path.exists(training_file):
            print('reading labeled examples from ', training_file)
            with open(training_file) as tf:
                linker.prepare_training(data_1,
                                        data_2,
                                        training_file=tf,
                                        sample_size=2)
        else:
            linker.prepare_training(data_1, data_2, sample_size=1000)

        print('starting active labeling...')

        dedupe.console_label(linker)

        linker.train()

        with open(training_file, 'w') as tf:
            linker.write_training(tf)

        with open(settings_file, 'wb') as sf:
            linker.write_settings(sf)

    print('clustering...')
    linked_records = linker.join(data_1, data_2, 0.9, constraint='many-to-many')

    print('# duplicate sets', len(linked_records))

    cluster_membership = {}
    for cluster_id, (cluster, score) in enumerate(linked_records):
        for record_id in cluster:
            cluster_membership[record_id] = {'Cluster ID': cluster_id,
                                             'Link Score': score}

    #G.add_edge(1, 2, weight=4.7)
    #G.add_edges_from([(3, 4), (4, 5)], color="red")


    print('test')

# 1. PREP TABLE FOR DEDUPE
# FOR PEOPLE, JOBS RECORD LINKAGES:
    # 2. SPECIFY SETTINGS IN YAML
    # 3. SPECIFY PERFECT MATCH VARS FOR SQL IN YAML
    # 4. USE PERFECT MATCHES AND DEDUPE MATCHES TO SAVE TABLE
    #   ID1, ID2, MATCHSCORE, DATE
    #   MARKED AS 1 IF FROM PERFECT SQL MATCH OR TRAINED DATA
# 5. USE FOR NETWORKX LINKAGE https://stackoverflow.com/questions/41534081/unique-id-for-network-clusters
#   GET UID FOR NETWORKS
#   ID, PERSONID, JOBID
#   FEEDS BACK INTO ORIGINAL PREPPED TABLE FOR FUTURE MATCHES

# FOR EACH NEW LINKAGE GROUP - IF ID IS NOT NEW ID - FIND LINKAGE AND ASSOCIATED ID IN SOURCE TABLE
# ASSIGN RECORD ID BASED ON NEW LINKAGE TO EACH RECORD - KEEPS PROCESSING DOWN
# ADD TO TABLE

