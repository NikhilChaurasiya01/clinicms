# Generated migration file - save as: appointments/migrations/000X_add_is_rescheduled.py

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0001_initial'),  # Replace with your last migration number
    ]

    operations = [
        migrations.AddField(
            model_name='appointment',
            name='is_rescheduled',
            field=models.BooleanField(default=False, help_text='True if this appointment has been rescheduled'),
        ),
    ]