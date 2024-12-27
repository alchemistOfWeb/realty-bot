# Generated by Django 5.1.3 on 2024-12-10 10:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('botmodels', '0002_groupprofile_deleted'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userprofile',
            name='name',
        ),
        migrations.AddField(
            model_name='userprofile',
            name='chat_id',
            field=models.BigIntegerField(null=True, unique=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='username',
            field=models.CharField(default='', max_length=255),
        ),
        migrations.CreateModel(
            name='TgSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('end_sending_time', models.TimeField(null=True)),
                ('start_sending_time', models.TimeField(null=True)),
                ('period_sending_time', models.TimeField(null=True)),
                ('do_sending', models.BooleanField(default=False)),
                ('user_profile', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bot_setting', to='botmodels.userprofile')),
            ],
        ),
    ]