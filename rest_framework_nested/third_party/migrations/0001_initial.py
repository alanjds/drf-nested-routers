# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Headline',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(max_length=256)),
                ('post_date', models.DateField(null=True)),
                ('digest', models.CharField(max_length=256, null=True)),
                ('title', models.CharField(unique=True, max_length=64)),
                ('score', models.IntegerField()),
            ],
            options={
                'db_table': 'headline',
            },
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(unique=True, max_length=64)),
                ('auth', models.OneToOneField(related_name='custom_info', verbose_name='User', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'user',
            },
        ),
        migrations.CreateModel(
            name='UserWebSite',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('importance', models.IntegerField(null=True)),
                ('user', models.ForeignKey(to='third_party.User')),
            ],
            options={
                'db_table': 'user_website',
            },
        ),
        migrations.CreateModel(
            name='WebSite',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(max_length=256)),
                ('name', models.CharField(unique=True, max_length=64)),
                ('tags', models.CharField(max_length=128, null=True)),
            ],
            options={
                'db_table': 'website',
            },
        ),
        migrations.AddField(
            model_name='userwebsite',
            name='website',
            field=models.ForeignKey(to='third_party.WebSite'),
        ),
        migrations.AddField(
            model_name='headline',
            name='website_id',
            field=models.ForeignKey(to='third_party.WebSite', db_column=b'website_id'),
        ),
    ]
