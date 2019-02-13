# Generated by Django 2.1.5 on 2019-02-11 16:21

from django.db import migrations, models
import django.db.models.deletion
import feincms3.cleanse
import imagefield.fields
import shared.media_archive.models
import shared.utils.models.slugs


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Download',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('image', 'Image'), ('video', 'Video'), ('audio', 'Audio'), ('pdf', 'PDF document'), ('swf', 'Flash'), ('txt', 'Text'), ('rtf', 'Rich Text'), ('zip', 'Zip archive'), ('doc', 'Microsoft Word'), ('xls', 'Microsoft Excel'), ('ppt', 'Microsoft PowerPoint'), ('other', 'Binary')], editable=False, max_length=12, verbose_name='file type')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Hochgeladen')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Geändert')),
                ('is_public', models.BooleanField(default=True, help_text='Nur als "öffentlich sichtbar" markierte Mediendaten werden öffentlich angezeigt.', verbose_name='Veröffentlicht')),
                ('file_size', models.IntegerField(blank=True, editable=False, null=True, verbose_name='file size')),
                ('slug', shared.utils.models.slugs.DowngradingSlugField(blank=True, help_text='Kurzfassung des Namens für die Adresszeile im Browser. Vorzugsweise englisch, keine Umlaute, nur Bindestrich als Sonderzeichen.')),
                ('name', models.CharField(blank=True, max_length=200, null=True, verbose_name='Name')),
                ('caption', feincms3.cleanse.CleansedRichTextField(blank=True, verbose_name='Bildunterschrift')),
                ('credits', models.CharField(blank=True, max_length=500, null=True, verbose_name='Credits')),
                ('copyright', models.CharField(blank=True, max_length=2000, verbose_name='Rechteinhaber/in')),
                ('file', models.FileField(upload_to='', verbose_name='Datei')),
            ],
            options={
                'verbose_name': 'Download',
                'verbose_name_plural': 'Downloads',
                'ordering': ['name'],
            },
            bases=(shared.media_archive.models.DeleteOldFileMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Gallery',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('internal_name', models.CharField(help_text='Internal use only, not publicly visible.', max_length=500, verbose_name='Internal Name')),
                ('name', models.CharField(blank=True, help_text='Publicly visible name.', max_length=200, null=True, verbose_name='Name')),
                ('slug', models.SlugField(blank=True, null=True, verbose_name='Slug')),
                ('credits', models.CharField(blank=True, max_length=500, null=True, verbose_name='Credits')),
                ('caption', feincms3.cleanse.CleansedRichTextField(blank=True, null=True, verbose_name='Caption')),
                ('is_public', models.BooleanField(default=False, verbose_name='Active')),
                ('order_index', models.PositiveIntegerField(default=0, verbose_name='Order Index')),
            ],
            options={
                'verbose_name': 'Image Gallery',
                'verbose_name_plural': 'Image Galleries',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Image',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Hochgeladen')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='Geändert')),
                ('is_public', models.BooleanField(default=True, help_text='Nur als "öffentlich sichtbar" markierte Mediendaten werden öffentlich angezeigt.', verbose_name='Veröffentlicht')),
                ('file_size', models.IntegerField(blank=True, editable=False, null=True, verbose_name='file size')),
                ('slug', shared.utils.models.slugs.DowngradingSlugField(blank=True, help_text='Kurzfassung des Namens für die Adresszeile im Browser. Vorzugsweise englisch, keine Umlaute, nur Bindestrich als Sonderzeichen.')),
                ('name', models.CharField(blank=True, max_length=200, null=True, verbose_name='Name')),
                ('caption', feincms3.cleanse.CleansedRichTextField(blank=True, verbose_name='Bildunterschrift')),
                ('credits', models.CharField(blank=True, max_length=500, null=True, verbose_name='Credits')),
                ('copyright', models.CharField(blank=True, max_length=2000, verbose_name='Rechteinhaber/in')),
                ('image_width', models.PositiveIntegerField(blank=True, editable=False, null=True, verbose_name='image width')),
                ('image_height', models.PositiveIntegerField(blank=True, editable=False, null=True, verbose_name='image height')),
                ('image_ppoi', imagefield.fields.PPOIField(default='0.5x0.5', max_length=20, verbose_name='primary point of interest')),
                ('file', imagefield.fields.ImageField(blank=True, height_field='image_height', upload_to='', verbose_name='image', width_field='image_width')),
            ],
            options={
                'verbose_name': 'Bild',
                'verbose_name_plural': 'Bilder',
                'ordering': ['imagegalleryrel__position'],
            },
            bases=(shared.media_archive.models.DeleteOldFileMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ImageGalleryRel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(default=0)),
                ('gallery', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='media_archive.Gallery')),
                ('image', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='media_archive.Image')),
            ],
            options={
                'verbose_name': 'Bild',
                'verbose_name_plural': 'Bilder',
                'ordering': ['position'],
            },
        ),
        migrations.CreateModel(
            name='MediaCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('slug', models.SlugField(max_length=150, verbose_name='slug')),
                ('parent', models.ForeignKey(blank=True, limit_choices_to={'parent__isnull': True}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='media_archive.MediaCategory', verbose_name='Übergeordnet')),
            ],
            options={
                'verbose_name': 'Working Folder',
                'verbose_name_plural': 'Working Folders',
                'ordering': ['parent__name', 'name'],
            },
        ),
        migrations.CreateModel(
            name='MediaRole',
            fields=[
                ('id_text', models.CharField(help_text='Dieser Wert wird in der Programmierung benutzt und darf nicht verändert werden.', max_length=20, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200, verbose_name='name')),
            ],
            options={
                'verbose_name': 'Bild-Typ',
                'verbose_name_plural': 'Bild-Typen',
                'ordering': ['name'],
            },
        ),
        migrations.AddField(
            model_name='image',
            name='categories',
            field=models.ManyToManyField(blank=True, to='media_archive.MediaCategory', verbose_name='Arbeitsmappe'),
        ),
        migrations.AddField(
            model_name='image',
            name='role',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='media_archive.MediaRole', verbose_name='Typ'),
        ),
        migrations.AddField(
            model_name='gallery',
            name='images',
            field=models.ManyToManyField(blank=True, through='media_archive.ImageGalleryRel', to='media_archive.Image', verbose_name='Images'),
        ),
        migrations.AddField(
            model_name='download',
            name='categories',
            field=models.ManyToManyField(blank=True, to='media_archive.MediaCategory', verbose_name='Arbeitsmappe'),
        ),
        migrations.AddField(
            model_name='download',
            name='role',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='media_archive.MediaRole', verbose_name='Typ'),
        ),
    ]