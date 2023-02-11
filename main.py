from datetime import datetime

from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableClient


def generate_entities(start_index: int, count: int):
    e = []
    for i in range(start_index, start_index + count):
        e.append({
            'startIndex': start_index,
            'currentIndex': i
            })
    return e


def to_entity(i, e):
    e["PartitionKey"] = 'basic'
    e["RowKey"] = str(i)
    return e


def basic_upsert(i, e):
    table_client = get_table_client('basic')
    entity = to_entity(i, e)
    table_client.upsert_entity(entity)


def process(items):
    for i, e in enumerate(items):
        basic_upsert(i, e)
        if i % 50 == 0:
            print("processing entity with index %d" % i)
    print("Done, processed a total of %d entities" % len(items))


def get_table_client(table_name: str):
    connection_string = 'UseDevelopmentStorage=true'
    table_client = TableClient.from_connection_string(conn_str=connection_string,table_name=table_name)
    try:
        table_client.create_table()
        print('table %s created successfully' % table_name)
    except ResourceExistsError:
        # print('table %s already exists' % table_name)
        pass
    return table_client


if __name__ == '__main__':
    n = 1000
    entities = generate_entities(0, n)
    start_time = datetime.now()
    process(entities)
    execution_time = datetime.now() - start_time
    eps = float(n) / execution_time.total_seconds()
    milliseconds = execution_time.microseconds / 1000
    print(f"Finished saving {n:d} entities in {milliseconds:d}ms ({eps:f} entities per second)")

