# Generated by Django 3.1.3 on 2020-11-29 12:44

from django.db import migrations, models
import name_assigner.models


class Migration(migrations.Migration):

    dependencies = [
        ('name_assigner', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team_details',
            name='file',
            field=models.FileField(upload_to='files', validators=[name_assigner.models.validate_file_extension]),
        ),
    ]
