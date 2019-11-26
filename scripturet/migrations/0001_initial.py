from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import scripturet.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Approval',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('step', models.CharField(choices=[('translation', 'Translation'), ('verification', 'Verification'), ('chapter_verification', 'Chapter verification'), ('oral_verification', 'Oral verification')], max_length=32)),
                ('approved', models.BooleanField(default=True)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('approver', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['date_created'],
                'permissions': [('handle_own_approval', "Can approve and disapprove in user's own name")],
            },
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('book_code', models.CharField(max_length=3, unique=True, validators=[scripturet.models.validate_uppercase])),
                ('book_name', models.CharField(max_length=1024, unique=True)),
                ('book_number', models.IntegerField(unique=True)),
                ('chapters', models.IntegerField()),
            ],
            options={
                'ordering': ['book_number'],
            },
        ),
        migrations.CreateModel(
            name='Verse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('translation_code', models.CharField(max_length=3, validators=[scripturet.models.validate_uppercase])),
                ('chapter_number', models.IntegerField()),
                ('verse_number', models.IntegerField()),
                ('text', models.TextField()),
                ('published', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('approvers', models.ManyToManyField(through='scripturet.Approval', to=settings.AUTH_USER_MODEL)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='scripturet.Book')),
            ],
            options={
                'ordering': ['book', 'chapter_number', 'verse_number', 'translation_code'],
                'permissions': [('propose_verse', 'Can propose a translation revision to a verse')],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile_pic_url', models.URLField(blank=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('comment_text', models.TextField()),
                ('resolved', models.BooleanField(default=False)),
                ('hidden', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='comment_children', to='scripturet.Comment')),
            ],
            options={
                'ordering': ['date_created'],
                'permissions': [('handle_own_comment', "Can make, modify and delete comments in user's own name")],
            },
        ),
        migrations.CreateModel(
            name='Claim',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chapter_number', models.IntegerField()),
                ('verse_number', models.IntegerField()),
                ('step', models.CharField(choices=[('translation', 'Translation'), ('verification', 'Verification'), ('chapter_verification', 'Chapter verification'), ('oral_verification', 'Oral verification')], max_length=32)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('finished', models.BooleanField(default=False)),
                ('book', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='scripturet.Book')),
                ('claimer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['book', 'chapter_number', 'verse_number', 'date_created', 'claimer'],
                'permissions': [('handle_own_claim', "Can claim and remove claim in user's own name")],
            },
        ),
        migrations.CreateModel(
            name='CategoryReview',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(max_length=32)),
                ('date_created', models.DateTimeField(default=django.utils.timezone.now)),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL)),
                ('verse', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='scripturet.Verse')),
            ],
            options={
                'permissions': [('handle_own_categoryreview', "Can add and remove category reviews in user's own name")],
            },
        ),
        migrations.AddField(
            model_name='approval',
            name='verse',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='scripturet.Verse'),
        ),
        migrations.AddIndex(
            model_name='verse',
            index=models.Index(fields=['book', 'chapter_number', 'verse_number'], name='scripturet__book_id_08b794_idx'),
        ),
        migrations.AddIndex(
            model_name='claim',
            index=models.Index(fields=['book', 'chapter_number', 'verse_number'], name='scripturet__book_id_cb0e6e_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='categoryreview',
            unique_together={('verse', 'author', 'category')},
        ),
        migrations.AlterUniqueTogether(
            name='approval',
            unique_together={('approver', 'verse', 'step')},
        ),
    ]
