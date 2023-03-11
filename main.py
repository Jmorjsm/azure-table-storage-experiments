import asyncio
from datetime import datetime

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


def to_partitioned_entity(i, e, modulo=10):
    partition = i % modulo
    e["PartitionKey"] = f'batch_{partition:d}'
    e["RowKey"] = str(i)
    return str(partition), e


def basic_upsert(items):
    table_client = get_table_client('basic')
    for i, e in enumerate(items):
        entity = to_basic_entity(i, e)
        table_client.upsert_entity(entity)

        if i % 500 == 0:
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


def batch_upsert_partitioned(items, batch_size=100, partition_modulo=10):
    partitioned_operations = {}
    for i, e in enumerate(items):
        p, entity = to_partitioned_entity(i, e, partition_modulo)

        # Create the operations list for this partition if it doesn't exist.
        if p not in partitioned_operations:
            partitioned_operations[p] = []
        partition = partitioned_operations[p]
        partition.append(('upsert', entity))
        if i % 500 == 0:
            print("\tProcessing entity with index %d" % i)

        if len(partition) == batch_size:
            submit_partition(partitioned_operations, p, partition_modulo)
    # Clean up any partitions with outstanding operations.
    for p in partitioned_operations:
        submit_partition(partitioned_operations, p, partition_modulo)
    print("Done, processed a total of %d entities" % len(items))


async def batch_upsert_partitioned_async(items, batch_size=100, partition_modulo=10):
    partitioned_operations = {}
    for i, e in enumerate(items):
        p, entity = to_partitioned_entity(i, e, partition_modulo)

        # Create the operations list this partition if it doesn't exist.
        if p not in partitioned_operations:
            partitioned_operations[p] = []
        partition = partitioned_operations[p]
        partition.append(('upsert', entity))
        if i % 500 == 0:
            print("\tProcessing entity with index %d" % i)

        if len(partition) == batch_size:
            await submit_partition_async(partitioned_operations, p, partition_modulo)
    # Clean up any partitions with outstanding operations.
    for p in partitioned_operations:
        await submit_partition_async(partitioned_operations, p, partition_modulo)
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


async def submit_partition_async(partitioned_operations, p, partition_modulo):
    partition = partitioned_operations[p]
    if len(partition) == 0:
        return

    table_client = await get_table_client_async(f'batchPartitioned{partition_modulo:d}')
    try:
        await table_client.submit_transaction(partition)
        partitioned_operations[p] = []
    except TableTransactionError as e:
        print("Failed to submit transaction")
        raise e


def get_table_client(table_name: str):
    connection_string = 'UseDevelopmentStorage=true'
    table_client = TableClient.from_connection_string(conn_str=connection_string, table_name=table_name)
    try:
        table_client.create_table()
        print('table %s created successfully' % table_name)
    except ResourceExistsError:
        # print('table %s already exists' % table_name)
        pass
    return table_client


async def get_table_client_async(table_name: str):
    connection_string = 'UseDevelopmentStorage=true'
    table_client = TableClient.from_connection_string(conn_str=connection_string, table_name=table_name)
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


async def run_test_async(n, insert_function, *args):
    print("Starting insert test for function %s with %d entities." % (insert_function.__name__, n))
    entities = generate_entities(0, n)
    start_time = datetime.now()

    await insert_function(entities, *args)
    execution_time = datetime.now() - start_time
    total_seconds = execution_time.total_seconds()
    eps = float(n) / total_seconds
    print(f"Finished test for function {insert_function.__name__:s} saving {n:d} entities in {total_seconds:f}s "
          f"({eps:f} entities per second)")

if __name__ == '__main__':
    # test with 300k entities, 4 props, 40,40,300,100 chars respectively
    #n_entities = 300000
    n_entities = 10000
    property_shapes = (40, 40, 300, 100)

    # run_test(n_entities, basic_upsert)
    # run_test(n_entities, batch_upsert)
    #run_test(n_entities, batch_upsert_partitioned, 100, 1000)
    asyncio.run(run_test_async(n_entities, batch_upsert_partitioned_async, 100, 1000))
