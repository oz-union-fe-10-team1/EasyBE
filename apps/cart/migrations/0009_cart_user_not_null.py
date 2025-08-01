import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cart", "0008_remove_cart_customer_cart_user"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cart",
            name="user",
            field=models.OneToOneField(
                to="users.User", on_delete=django.db.models.deletion.CASCADE, related_name="cart", verbose_name="사용자"
            ),
        ),
    ]
