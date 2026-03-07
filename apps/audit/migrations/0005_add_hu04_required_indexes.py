from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0004_alter_auditlog_action_type'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['content_type', 'object_id'], name='audit_ct_obj_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user'], name='audit_user_idx'),
        ),
        migrations.RemoveIndex(
            model_name='auditlog',
            name='audit_audit_created_6e540c_idx',
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['created_at'], name='audit_created_idx'),
        ),
    ]
