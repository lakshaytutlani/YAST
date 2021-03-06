# -*- coding: utf-8 -*-
# Generated by Django 1.11.12 on 2018-09-08 14:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('login', '0005_need_blood_user_lookup_key'),
    ]

    operations = [
        migrations.CreateModel(
            name='active_campaigns',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('CAMPAIGN_ID', models.CharField(max_length=100)),
                ('ZIP', models.CharField(max_length=100)),
                ('ADDRESS', models.CharField(max_length=100)),
                ('CITY', models.CharField(max_length=100)),
                ('STATE', models.CharField(max_length=100)),
                ('LONGITUDE', models.CharField(max_length=100)),
                ('LATITUDE', models.CharField(max_length=100)),
                ('CHAIN_ID', models.CharField(max_length=100)),
                ('DATE', models.CharField(max_length=100)),
                ('SLOTS', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'active_campaigns',
            },
        ),
    ]
