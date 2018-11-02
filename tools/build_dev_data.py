if __name__ == "__main__":
    import django

    django.setup()
    from django.contrib.auth import get_user_model

    User = get_user_model()

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
