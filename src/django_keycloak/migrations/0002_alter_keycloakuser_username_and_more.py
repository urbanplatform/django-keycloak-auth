# Generated by Django 4.1.2 on 2023-02-07 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_keycloak", "0001_redo_migrations_0001to0005"),
    ]

    operations = [
        migrations.AlterField(
            model_name="keycloakuser",
            name="username",
            field=models.CharField(max_length=32, unique=True, verbose_name="username"),
        ),
        migrations.AlterField(
            model_name="keycloakuserautoid",
            name="username",
            field=models.CharField(max_length=32, unique=True, verbose_name="username"),
        ),
    ]
