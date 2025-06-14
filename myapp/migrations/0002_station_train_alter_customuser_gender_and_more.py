# Generated by Django 5.1.1 on 2025-02-11 19:49

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('station_code', models.CharField(max_length=10, unique=True)),
                ('station_name', models.CharField(max_length=100)),
                ('state', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='Train',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('train_number', models.CharField(max_length=10, unique=True)),
                ('train_name', models.CharField(max_length=100)),
                ('total_seats', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.AlterField(
            model_name='customuser',
            name='gender',
            field=models.CharField(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')], default='Male', max_length=10),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='user_profile_image',
            field=models.ImageField(default='profile/4.jpg', upload_to='profile'),
        ),
        migrations.CreateModel(
            name='Coach',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('coach_name', models.CharField(max_length=5)),
                ('coach_type', models.CharField(choices=[('AC', 'AC'), ('Sleeper', 'Sleeper'), ('General', 'General')], max_length=10)),
                ('coach_seats', models.PositiveIntegerField(default=0)),
                ('train', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='coaches', to='myapp.train')),
            ],
        ),
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sequence', models.PositiveIntegerField()),
                ('platform_no', models.PositiveIntegerField(default=0)),
                ('day_of_week', models.IntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')], default=0)),
                ('arrival_time', models.TimeField(default=datetime.time(0, 0))),
                ('departure_time', models.TimeField(default=datetime.time(0, 0))),
                ('departure_next_day', models.BooleanField(default=False)),
                ('step_distance', models.FloatField(blank=True, help_text='Distance in kilometers', null=True)),
                ('station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='routes', to='myapp.station')),
                ('train', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='routes', to='myapp.train')),
            ],
            options={
                'ordering': ['train', 'sequence', 'arrival_time'],
                'unique_together': {('train', 'station', 'sequence', 'platform_no')},
            },
        ),
    ]
