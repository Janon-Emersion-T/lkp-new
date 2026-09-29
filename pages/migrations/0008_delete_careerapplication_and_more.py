import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hr", "0001_initial"),
        ("pages", "0007_remove_websitesection_page_delete_mediaasset_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(
                    name="CareerApplication",
                ),
                migrations.AlterField(
                    model_name="supportticket",
                    name="assigned_to",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="hr.employee",
                    ),
                ),
                migrations.AlterField(
                    model_name="projecttask",
                    name="employee",
                    field=models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tasks",
                        to="hr.employee",
                    ),
                ),
                migrations.RemoveField(
                    model_name="project",
                    name="team",
                ),
                migrations.DeleteModel(
                    name="Employee",
                ),
                migrations.AddField(
                    model_name="project",
                    name="team",
                    field=models.ManyToManyField(
                        blank=True,
                        related_name="projects",
                        to="hr.employee",
                    ),
                ),
            ],
        ),
    ]
