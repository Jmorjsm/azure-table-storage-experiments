import asyncio
from datetime import datetime

from azure.core.exceptions import ResourceExistsError
from azure.data.tables import TableTransactionError
from tabulate import tabulate
from tqdm import tqdm


def generate_entities(start_index: int, count: int, property_shapes: tuple):
    from random import choice
    from string import ascii_lowercase

    entities = []
    for i in range(start_index, start_index + count):
        entity = {
            'startIndex': start_index,
            'currentIndex': i
        }

        for prop_index, prop_size in enumerate(property_shapes):
            entity[f'p{prop_index}'] = "".join(choice(ascii_lowercase) for _ in range(prop_size))

        entities.append(entity)
    return entities


def to_basic_entity(i, e):
    e["PartitionKey"] = 'basic'
    e["RowKey"] = str(i)
    return e


def to_partitioned_entity(i, e, modulo=10):
    partition = i % modulo
    e["PartitionKey"] = f'batch_{partition:d}'
    e["RowKey"] = str(i)
    return str(partition), e


def basic_upsert(items):
    table_client = get_table_client('basic')
    for i, e in enumerate(tqdm(items)):
        entity = to_basic_entity(i, e)
        table_client.upsert_entity(entity)

        # if i % 500 == 0:
        #     print("\tProcessing entity with index %d" % i)
    print("Done, processed a total of %d entities" % len(items))


def batch_upsert(items, batch_size=100):
    operations = []
    for i, e in enumerate(tqdm(items)):
        entity = to_basic_entity(i, e)
        operations.append(('upsert', entity))
        # if i % 500 == 0:
        #     print("\tProcessing entity with index %d" % i)

        if i % batch_size == 0:
            table_client = get_table_client('batch')
            try:
                table_client.submit_transaction(operations)
                operations = []
            except TableTransactionError as e:
                print("Failed to submit transaction")
                raise e
    print("Done, processed a total of %d entities" % len(items))


def batch_upsert_partitioned(items, batch_size=100, partition_modulo=10):
    partitioned_operations = {}
    for i, e in enumerate(tqdm(items)):
        p, entity = to_partitioned_entity(i, e, partition_modulo)

        # Create the operations list for this partition if it doesn't exist.
        if p not in partitioned_operations:
            partitioned_operations[p] = []
        partition = partitioned_operations[p]
        partition.append(('upsert', entity))
        # if i % 500 == 0:
        #     print("\tProcessing entity with index %d" % i)

        if len(partition) == batch_size:
            submit_partition(partitioned_operations, p, partition_modulo)
    # Clean up any partitions with outstanding operations.
    for p in partitioned_operations:
        submit_partition(partitioned_operations, p, partition_modulo)
    print("Done, processed a total of %d entities" % len(items))


async def batch_upsert_partitioned_async(items, batch_size=100, partition_modulo=10):
    from azure.data.tables.aio import TableClient
    connection_string = 'UseDevelopmentStorage=true'
    table_name = f'batchPartitioned{partition_modulo:d}'f'batchPartitioned{partition_modulo:d}'
    table_client = TableClient.from_connection_string(conn_str=connection_string, table_name=table_name)
    try:
        await table_client.create_table()
        print('table %s created successfully' % table_name)
    except ResourceExistsError:
        print('table %s already exists' % table_name)
        pass

    partitioned_operations = {}
    for i, e in enumerate(tqdm(items)):
        p, entity = to_partitioned_entity(i, e, partition_modulo)

        # Create the operations list this partition if it doesn't exist.
        if p not in partitioned_operations:
            partitioned_operations[p] = []
        partition = partitioned_operations[p]
        partition.append(('upsert', entity))
        # if i % 500 == 0:
        #     print("\tProcessing entity with index %d" % i)

        if len(partition) == batch_size:
            await submit_partition_async(partitioned_operations, p, partition_modulo, table_client)
    # Clean up any partitions with outstanding operations.
    for p in partitioned_operations:
        await submit_partition_async(partitioned_operations, p, partition_modulo, table_client)

    await table_client.__aexit__()
    print("Done, processed a total of %d entities" % len(items))


def submit_partition(partitioned_operations, p, partition_modulo):
    partition = partitioned_operations[p]
    if len(partition) == 0:
        return

    table_client = get_table_client(f'batchPartitioned{partition_modulo:d}')
    try:
        table_client.submit_transaction(partition)
        partitioned_operations[p] = []
    except TableTransactionError as e:
        print("Failed to submit transaction")
        raise e


async def submit_partition_async(partitioned_operations, p, partition_modulo, table_client):
    partition = partitioned_operations[p]
    if len(partition) == 0:
        return

    try:
        await table_client.submit_transaction(partition)
        partitioned_operations[p] = []
    except TableTransactionError as e:
        print("Failed to submit transaction")
        raise e


def get_connection_string():
    from os import environ
    return environ.get('TABLE_STORAGE_CONNECTION_STRING', 'UseDevelopmentStorage=true')


def get_table_client(table_name: str):
    from azure.data.tables import TableClient
    connection_string = get_connection_string()
    table_client = TableClient.from_connection_string(conn_str=connection_string, table_name=table_name)
    try:
        table_client.create_table()
        print('table %s created successfully' % table_name)
    except ResourceExistsError:
        # print('table %s already exists' % table_name)
        pass
    return table_client


async def get_table_client_async(table_name: str):
    from azure.data.tables.aio import TableClient
    connection_string = get_connection_string()
    table_client = TableClient.from_connection_string(conn_str=connection_string, table_name=table_name)
    try:
        return await table_client.create_table()
        print('table %s created successfully' % table_name)
    except ResourceExistsError:
        # print('table %s already exists' % table_name)
        pass
    except:
        try:
            table_client.close()
        except:
            pass
        raise


def run_test(n, property_shapes, insert_function, *args):
    print("Starting insert test for function %s with %d entities." % (insert_function.__name__, n))
    entities = generate_entities(0, n, property_shapes)
    start_time = datetime.now()

    insert_function(entities, *args)
    execution_time = datetime.now() - start_time
    total_seconds = execution_time.total_seconds()
    eps = float(n) / total_seconds
    print(f"Finished test for function {insert_function.__name__:s} saving {n:d} entities in {total_seconds:f}s "
          f"({eps:f} entities per second)")

    return (total_seconds, eps, insert_function.__name__) + args


async def run_test_async(n, property_shapes, insert_function, *args):
    print("Starting insert test for function %s with %d entities." % (insert_function.__name__, n))
    entities = generate_entities(0, n, property_shapes)
    start_time = datetime.now()

    await insert_function(entities, *args)
    execution_time = datetime.now() - start_time
    total_seconds = execution_time.total_seconds()
    eps = float(n) / total_seconds
    print(f"Finished test for function {insert_function.__name__:s} saving {n:d} entities in {total_seconds:f}s "
          f"({eps:f} entities per second)")

    return (total_seconds, eps, insert_function.__name__) + args

def cleanup():
    from azure.data.tables import TableServiceClient
    connection_string = get_connection_string()
    table_service_client = TableServiceClient.from_connection_string(connection_string)

    for table in table_service_client.list_tables():
        print(f'deleting table {table.name}')
        table_service_client.delete_table(table.name)

if __name__ == '__main__':
    cleanup()
    # test with 300k entities, 4 props, 40,40,300,100 chars respectively
    #n_entities = 300000
    n_entities = 300
    property_shapes = (40, 40, 300, 100)

    results = []
    results.append(run_test(n_entities, property_shapes, basic_upsert))
    results.append(run_test(n_entities, property_shapes, batch_upsert))
    partition_counts = (100, 200, 500, 1000, 2000, 2500, 5000)
    for partition_count in partition_counts:
        results.append(run_test(n_entities, property_shapes, batch_upsert_partitioned, 100, partition_count))

    for partition_count in partition_counts:
        results.append(asyncio.run(run_test_async(n_entities, property_shapes, batch_upsert_partitioned_async, 100, partition_count)))

    print(tabulate(results, headers=["Time elapsed(s)", "Entities/second", "Function", "Partition size", "Partition count"]))
