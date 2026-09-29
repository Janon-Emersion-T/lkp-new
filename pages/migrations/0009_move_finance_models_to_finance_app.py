from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
        ('pages', '0008_delete_careerapplication_and_more'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name='Payment'),
                migrations.DeleteModel(name='Expense'),
                migrations.DeleteModel(name='Invoice'),
            ],
        ),
    ]
