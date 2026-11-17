
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0003_repair_created_at'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='product',
                    name='created_at',
                    field=models.DateTimeField(auto_now_add=True),
                ),
            ],
        ),
    ]
