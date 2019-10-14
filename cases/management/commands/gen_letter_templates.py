import os
import re

from django.conf import settings
from django.core.management.base import BaseCommand

from cases.models import LetterTemplate


class Command(BaseCommand):
    def handle(self, *args, **options):
        path_regex = re.compile(settings.NRQZ_LETTER_TEMPLATE_REGEX)
        paths_on_disk = set(
            os.path.join(settings.NRQZ_LETTER_TEMPLATE_DIR, path)
            for path in os.listdir(settings.NRQZ_LETTER_TEMPLATE_DIR)
            if path_regex.match(path)
        )

        known_paths = set(LetterTemplate.objects.values_list("path", flat=True))
        unknown_paths = paths_on_disk.difference(known_paths)

        for path in unknown_paths:
            lt = LetterTemplate.objects.create(
                path=path,
                name=os.path.basename(path),
                description=(
                    f"Auto-created for file {path}. Feel free to give "
                    "me a more useful description!"
                ),
            )
            print(f"Created LetterTemplate {lt}")
