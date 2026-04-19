# portal/migrations/000X_add_portalcliente_access_fields.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attend", "0008_plano_portalcliente_customerinvitetoken_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="portalcliente",
            name="acesso_token",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="portalcliente",
            name="acesso_token_expira_em",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="portalcliente",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, null=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="portalcliente",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
            preserve_default=False,
        ),
    ]