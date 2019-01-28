import os

import django

django.setup()
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

from cases.models import LetterTemplate


def create_users():
    users = ["tchamber", "pwoody", "mholstin", "mwhitehe", "koneil"]

    for user in users:
        try:
            User.objects.create_user(
                username=user, password=user, is_staff=True, is_superuser=True
            )
        except django.db.utils.IntegrityError:
            print(f"{user} already exists!")
        else:
            print(f"{user} created")


def create_templates():
    for path in os.listdir(settings.NRQZ_LETTER_TEMPLATE_DIR):
        full_path = os.path.join(settings.NRQZ_LETTER_TEMPLATE_DIR, path)
        if os.path.isfile(full_path):
            lt, created = LetterTemplate.objects.get_or_create(
                name=os.path.basename(full_path), path=full_path
            )
            if created:
                print(f"Created {lt}")
            else:
                print(f"{lt} already exists!")


def main():
    create_users()
    create_templates()


if __name__ == "__main__":
    main()
