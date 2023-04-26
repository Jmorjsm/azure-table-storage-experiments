# azure-table-storage-experiments
Repo containing some experiments in azure table storage, mainly testing batch insert performance using various methods.

## Results
| elapsed | eps     | function                       | partitionSize |  partitionCount |
|---------|---------| ------------------------------ |---------------|-----------------|
| 2.91963 | 342.509 | batch_upsert                   | n/a           | n/a             |     
| 15.9524 | 62.6867 | batch_upsert_partitioned       | 100           | 100             |
| 28.7108 | 34.83   | batch_upsert_partitioned       | 100           | 200             |
| 66.311  | 15.0805 | batch_upsert_partitioned       | 100           | 500             |
| 134.702 | 7.42379 | batch_upsert_partitioned       | 100           | 1000            |
| 82.2025 | 12.1651 | batch_upsert_partitioned       | 100           | 2000            |
| 87.4439 | 11.4359 | batch_upsert_partitioned       | 100           | 2500            |
| 83.6264 | 11.9579 | batch_upsert_partitioned       | 100           | 5000            |
| 3.55084 | 281.623 | batch_upsert_partitioned_async | 100           | 100             |
| 5.05056 | 197.998 | batch_upsert_partitioned_async | 100           | 200             |
| 8.34641 | 119.812 | batch_upsert_partitioned_async | 100           | 500             |
| 14.7585 | 67.7576 | batch_upsert_partitioned_async | 100           | 1000            |
| 14.1735 | 70.5541 | batch_upsert_partitioned_async | 100           | 2000            |
| 14.6752 | 68.1423 | batch_upsert_partitioned_async | 100           | 2500            |
| 13.6486 | 73.2674 | batch_upsert_partitioned_async | 100           | 5000            |

## function descriptions
### batch_upsert
Standard batch insert, no partitioning.

### batch_upsert_partitioned
Batch insert, partitioned into `partitionCount` partitions.

### batch_upsert_partitioned_async
Async batch insert, partitioned into `partitionCount` partitions. Theoretically this should be faster than the synchronous `batch_upsert_partitioned` method.
