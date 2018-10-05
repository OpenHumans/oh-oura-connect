from django.db import migrations


def forwards_func(app_label, schema_editor):
    db_alias = schema_editor.connection.alias
    app_label.get_model("admin", "Administrator").objects.using(db_alias).create(
        user=app_label.get_model("auth", "User").objects.using(db_alias).create(
            username="admin",
            is_superuser=True,
        )
    )


def reverse_func(app_label, schema_editor):
    db_alias = schema_editor.connection.alias
    app_label.get_model("admin", "Administrator").objects.using(db_alias).filter(
        user__username="admin"
    ).delete()
    app_label.get_model("auth", "User").objects.using(db_alias).filter(
        username="admin"
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("admin", "0001_initial")
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func)
    ]
