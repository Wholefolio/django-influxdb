# Generated by Django 2.2 on 2021-11-26 03:20

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='InfluxTasks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=256, unique=True)),
                ('flux', models.TextField()),
                ('task_interval', models.CharField(max_length=50)),
                ('created', models.BooleanField(default=False)),
                ('destination_bucket', models.CharField(max_length=256)),
            ],
        ),
    ]
