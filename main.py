# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.


def generate_entities(start_index: int, count: int):
    e = []
    for i in range(start_index, start_index + count):
        e += {
            'start_index': start_index,
            'current_index': i
            }
    return e


def process(e):
    for i, e in enumerate(e):
        if i % 50 == 0:
            print("processing entity with index %d" % i)
    print("Done, processed a total of %d entities" % len(e))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    entities = generate_entities(0, 1000)
    process(entities)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
