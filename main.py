from time import time

from azure.data.tables import TableClient, TableTransactionError
from azure.core.exceptions import ResourceExistsError


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
    print(entity)
    table_client.upsert_entity(entity)


def process(items):
    print(items)
    for i, e in enumerate(items):
        print(type(e))
        print(e)
        basic_upsert(i, e)
        if i % 50 == 0:
            print("processing entity with index %d" % i)
    print("Done, processed a total of %d entities" % len(e))


def get_table_client(table_name: str):
    connection_string = 'UseDevelopmentStorage=true'
    table_client = TableClient.from_connection_string(conn_str=connection_string,table_name=table_name)
    try:
        table_client.create_table()
        print('table %s created successfully' % table_name)
    except ResourceExistsError:
        print('table %s already exists' % table_name)
    return table_client


if __name__ == '__main__':
    n = 1000
    entities = generate_entities(0, n)
    start_time = time()
    process(entities)
    execution_time = time() - start_time
    eps = n/(execution_time*1000)
    print("Finished saving %i entities in %dms (%d entities per second)" % (n, execution_time, eps))

