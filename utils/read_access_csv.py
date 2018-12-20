import csv


def load_rows(path):
    with open(path, newline="", encoding="latin1") as file:
        lines = file.readlines()

    return csv.DictReader(lines)
