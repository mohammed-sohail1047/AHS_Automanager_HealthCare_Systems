from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HclsWebApi', '0015_remove_adminlogin_createdon_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='Password',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='doctor',
            name='Status',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='helper',
            name='Password',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='helper',
            name='Status',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='receptionist',
            name='Password',
            field=models.CharField(blank=True, max_length=128, null=True),
        ),
        migrations.AddField(
            model_name='receptionist',
            name='Status',
            field=models.BooleanField(default=True),
        ),
    ]
