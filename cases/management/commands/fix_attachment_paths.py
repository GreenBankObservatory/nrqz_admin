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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.already_merged = set()

    def add_arguments(self, parser):
        parser.add_argument("--from-csv")
        parser.add_argument("--dry-run", action="store_true")

    def save_attachment(self, attachment_to_save):
        try:
            existing_attachment = Attachment.objects.get(
                file_path=attachment_to_save.file_path
            )
        except Attachment.DoesNotExist:
            attachment_to_save.save()
            attachment = attachment_to_save
            tqdm.write(f"  NEW {attachment.id}")
        else:
            tqdm.write(
                f"  MERGING {existing_attachment.id} and {attachment_to_save.id} (keep {existing_attachment.id})"
            )
            self.already_merged.update([existing_attachment.id, attachment_to_save.id])
            attachment = MergedModelInstance.create(
                existing_attachment,
                [attachment_to_save],
                # This deletes the merged instances
                keep_old=False,
            )

        return attachment

    @transaction.atomic
    def foo(self):
        report = {"fixed": set(), "skipped": set()}
        # Used for initial conversion
        # relative_prefix_regex = re.compile(r"^(?:\.+[/\\]+)+")
        # Then we decided to convert gbfiler stuff, too
        relative_prefix_regex = re.compile(r"^\\\\Gbfiler\\nrqz\\", re.IGNORECASE)
        manual_prefix_fixes = [
            "SWTAP",
            "CRON",
            "NRQZDOCS",
            "Site Inspection Worksheets",
        ]
        attachments = Attachment.objects.only("file_path")
        for attachment in tqdm(attachments, unit="attachment"):
            original_file_path = attachment.file_path
            # Unquote! Some attachments have %20 instead of space, for example
            new_file_path = unquote(original_file_path)
            # Replace any relative prefixes with absolute. e.g. '../../<path>'
            # would end up as Q:/<path>
            new_file_path = relative_prefix_regex.sub("Q:\\\\", new_file_path)

            if any(new_file_path.startswith(prefix) for prefix in manual_prefix_fixes):
                new_file_path = f"Q:\\{new_file_path}"
            if original_file_path != new_file_path:
                tqdm.write(
                    f"Path '{original_file_path}' has changed to "
                    f"'{new_file_path}'; saving!"
                )
                attachment.file_path = new_file_path
                attachment.comments = (
                    f"{attachment.comments}\n\n<PATHFIX>: Path has "
                    f"been changed from '{original_file_path}' to "
                    f"'{new_file_path}'</PATHFIX>"
                )
                self.save_attachment(attachment)
                report["fixed"].add(attachment.id)
            else:
                report["skipped"].add(attachment.id)

        return report

    @transaction.atomic
    def handle(self, *args, **options):
        if options["from_csv"]:
            self.check_file_paths(options["from_csv"])
        else:
            # self.gen_attachments_report()
            report = self.foo()
            print("Action summary:")
            for action, attachment_ids in report.items():
                print(f"  {action}: {len(attachment_ids)}")
                # for attachment in Attachment.objects.filter(id__in=attachment_ids):
                #     print("{}: {}".format(key, len(value)))

            valid_prefixes = ("http", "q")

            valid_attachments = Attachment.objects.none()
            for prefix in valid_prefixes:
                valid_attachments |= Attachment.objects.filter(
                    file_path__istartswith=prefix
                )

            print("Attachments that need manual action:")
            for attachment in Attachment.objects.exclude(
                id__in=valid_attachments.values("id")
            ):
                attachment_for = {}
                if attachment.cases.exists():
                    attachment_for["cases"] = [str(i) for i in attachment.cases.all()]
                if attachment.prelim_cases.exists():
                    attachment_for["prelim_cases"] = [
                        str(i) for i in attachment.prelim_cases.all()
                    ]
                if attachment.facilities.exists():
                    attachment_for["facilities"] = [
                        str(i) for i in attachment.facilities.all()
                    ]
                if attachment.prelim_facilities.exists():
                    attachment_for["prelim_facilities"] = [
                        str(i) for i in attachment.prelim_facilities.all()
                    ]
                print(
                    f"  '{attachment.file_path}': {attachment.id}, attachment for {attachment_for}"
                )

        transaction.set_rollback(options["dry_run"])

    def check_file_paths(self, csv_path):
        """Checks all paths in given CSV file to see if they exist on the filesystem

        Intended to be run on the client-side"""

        report = {"found_new_path": [], "found_old_path": [], "not_found": []}
        with open(csv_path) as file:
            csv_reader = csv.reader(file)
            for old_path, new_path in csv_reader:
                if os.path.isfile(new_path):
                    report["found_new_path"].append(new_path)
                elif os.path.isfile(old_path):
                    report["found_old_path"].append(old_path)
                else:
                    report["not_found"].append((old_path, new_path))

        for key, value in report.items():
            print("{}: {}".format(key, len(value)))
        # pprint(report)
