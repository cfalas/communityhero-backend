# Generated by Django 3.0.4 on 2020-04-04 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0010_product_productweight'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='ProductWeight',
            field=models.DecimalField(decimal_places=2, default=1.0, max_digits=3),
        ),
    ]
