# Generated by Django 3.0.4 on 2020-04-26 03:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0020_user_usermessenger'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='ProductWeight',
            field=models.FloatField(default=1.0),
        ),
    ]
