"""Utilities for "fixing" Attachment paths"""

import csv
import os
from pprint import pprint
import re
from urllib.parse import unquote

from tabulate import tabulate
from tqdm import tqdm


from django.db import transaction
from django.db.models import Value, CharField
from django.db.utils import IntegrityError
from django.core.management.base import BaseCommand

from django_super_deduper.merge import MergedModelInstance

from cases.models import Attachment


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("path")

    def handle(self, path, **options):
        with open(path, "w") as file:
            for file_path in Attachment.objects.values_list("file_path", flat=True):
                file.write(f"{file_path}\n")
