# Generated manually for HU04 alignment
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0003_remove_auditlog_audit_audit_user_id_292c79_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='action_type',
            field=models.CharField(
                choices=[
                    ('CREATE', 'Create'),
                    ('UPDATE', 'Update'),
                    ('DELETE', 'Delete'),
                    ('SOFT_DELETE', 'Soft Delete'),
                    ('RESTORE', 'Restore'),
                    ('STATUS_CHANGE', 'Status Change'),
                    ('ROLE_CHANGE', 'Role Change'),
                    ('LOGIN', 'Login'),
                    ('LOGOUT', 'Logout'),
                    ('UNKNOWN', 'Unknown'),
                ],
                default='UNKNOWN',
                max_length=50,
            ),
        ),
    ]
