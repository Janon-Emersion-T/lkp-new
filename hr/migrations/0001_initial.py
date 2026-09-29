from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("pages", "0007_remove_websitesection_page_delete_mediaasset_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name="CareerApplication",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("name", models.CharField(max_length=180)),
                        ("email", models.EmailField(max_length=254)),
                        ("phone", models.CharField(blank=True, max_length=80)),
                        ("position", models.CharField(max_length=180)),
                        (
                            "status",
                            models.CharField(
                                choices=[
                                    ("new", "New"),
                                    ("screening", "Screening"),
                                    ("interview", "Interview"),
                                    ("offer", "Offer"),
                                    ("rejected", "Rejected"),
                                ],
                                default="new",
                                max_length=20,
                            ),
                        ),
                        ("resume_url", models.CharField(blank=True, max_length=500)),
                        ("message", models.TextField(blank=True)),
                    ],
                    options={
                        "db_table": "pages_careerapplication",
                    },
                ),
                migrations.CreateModel(
                    name="Employee",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        ("created_at", models.DateTimeField(auto_now_add=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                        ("name", models.CharField(max_length=180)),
                        ("email", models.EmailField(max_length=254, unique=True)),
                        ("role", models.CharField(blank=True, max_length=160)),
                        (
                            "status",
                            models.CharField(
                                choices=[
                                    ("active", "Active"),
                                    ("on_leave", "On Leave"),
                                    ("inactive", "Inactive"),
                                ],
                                default="active",
                                max_length=20,
                            ),
                        ),
                        ("start_date", models.DateField(blank=True, null=True)),
                        ("notes", models.TextField(blank=True)),
                    ],
                    options={
                        "db_table": "pages_employee",
                    },
                ),
            ],
        ),
    ]
