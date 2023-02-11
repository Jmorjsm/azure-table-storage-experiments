from datetime import datetime
from math import floor

from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableClient, TableTransactionError


def generate_entities(start_index: int, count: int):
    e = []
    for i in range(start_index, start_index + count):
        e.append({
            'startIndex': start_index,
            'currentIndex': i
            })
    return e


def to_basic_entity(i, e):
    e["PartitionKey"] = 'basic'
    e["RowKey"] = str(i)
    return e


def basic_upsert(items):
    table_client = get_table_client('basic')
    for i, e in enumerate(items):
        entity = to_basic_entity(i, e)
        table_client.upsert_entity(entity)

        if i % 50 == 0:
            print("\tProcessing entity with index %d" % i)
    print("Done, processed a total of %d entities" % len(items))


def batch_upsert(items, batch_size=100):
    operations = []
    for i, e in enumerate(items):
        entity = to_basic_entity(i, e)
        operations.append(('upsert', entity))
        if i % 500 == 0:
            print("\tProcessing entity with index %d" % i)

        if i % batch_size == 0:
            table_client = get_table_client('batch')
            try:
                table_client.submit_transaction(operations)
                operations = []
            except TableTransactionError as e:
                print("Failed to submit transaction")
                raise e
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


def run_test(n, insert_function, *args):
    print("Starting insert test for function %s with %d entities." % (insert_function.__name__, n))
    entities = generate_entities(0, n)
    start_time = datetime.now()

    insert_function(entities, *args)
    execution_time = datetime.now() - start_time
    total_seconds = execution_time.total_seconds()
    eps = float(n) / total_seconds
    print(f"Finished test for function {insert_function.__name__:s} saving {n:d} entities in {total_seconds:f}s "
          f"({eps:f} entities per second)")


if __name__ == '__main__':
    n_entities = 10000
    # run_test(n_entities, basic_upsert)
    run_test(n_entities, batch_upsert)

