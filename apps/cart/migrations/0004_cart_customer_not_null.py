import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cart", "0003_remove_cart_session_key_remove_cart_user_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cart",
            name="customer",
            field=models.OneToOneField(
                to="users.User", on_delete=django.db.models.deletion.CASCADE, related_name="cart", verbose_name="고객"
            ),
        ),
    ]
