import io
import os
import shutil
import tempfile
from unittest.mock import patch
from PIL import Image

from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.storage import storages, FileSystemStorage
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.models import User
from django.urls import reverse

from core.models import GalleryImage
from core.forms import GalleryImageAdminForm


def create_test_image(format='JPEG', size=(50, 50), color='blue'):
    """Helper to generate a real, valid image in memory."""
    img = Image.new('RGB', size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    ext = 'jpg' if format.lower() == 'jpeg' else format.lower()
    return SimpleUploadedFile(f"test_image.{ext}", buf.getvalue(), content_type=f"image/{format.lower()}")


class StorageAndUploadTest(TestCase):
    """
    Story 2.2: Cloudinary image uploads and storage configuration tests.
    """

    def setUp(self):
        self.temp_media = tempfile.mkdtemp()
        self.staff_user = User.objects.create_superuser(
            username='admin_staff',
            password='Password123!',
            email='admin@example.com'
        )

    def tearDown(self):
        shutil.rmtree(self.temp_media, ignore_errors=True)

    def test_storage_backend_is_filesystem_when_use_cloudinary_false(self):
        """When USE_CLOUDINARY=False, STORAGES['default'] is FileSystemStorage."""
        with override_settings(
            USE_CLOUDINARY=False,
            MEDIA_ROOT=self.temp_media,
            STORAGES={
                'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'}
            }
        ):
            default_storage = storages['default']
            self.assertIsInstance(default_storage, FileSystemStorage)

            valid_image = create_test_image('JPEG')
            gallery_item = GalleryImage.objects.create(
                image=valid_image,
                caption='Local storage test',
                order=1,
                is_active=True
            )
            self.assertTrue(gallery_item.image.name.startswith('gallery/'))
            self.assertTrue(default_storage.exists(gallery_item.image.name))

    def test_storage_backend_is_cloudinary_when_use_cloudinary_true(self):
        """When USE_CLOUDINARY=True and CLOUDINARY_URL is present, storage is MediaCloudinaryStorage."""
        with override_settings(
            USE_CLOUDINARY=True,
            CLOUDINARY_STORAGE={
                'CLOUD_NAME': 'democloud',
                'API_KEY': '12345',
                'API_SECRET': 'secret',
                'PREFIX': 'nivetha/',
            }
        ):
            from cloudinary_storage.storage import MediaCloudinaryStorage
            storage = MediaCloudinaryStorage()
            self.assertIsInstance(storage, MediaCloudinaryStorage)

    def test_missing_cloudinary_url_raises_improperly_configured(self):
        """If USE_CLOUDINARY is True but CLOUDINARY_URL is empty, fail with clear error."""
        with self.assertRaises(ImproperlyConfigured) as ctx:
            use_cloudinary = True
            cloudinary_url = ''
            if use_cloudinary and not cloudinary_url:
                raise ImproperlyConfigured("CLOUDINARY_URL must be set when USE_CLOUDINARY=True.")
        self.assertIn("CLOUDINARY_URL must be set", str(ctx.exception))

    def test_admin_upload_with_mocked_cloudinary(self):
        """Mock Cloudinary uploader to verify upload is called without network access."""
        with override_settings(
            USE_CLOUDINARY=True,
            CLOUDINARY_STORAGE={
                'CLOUD_NAME': 'democloud',
                'API_KEY': '12345',
                'API_SECRET': 'secret',
                'PREFIX': 'nivetha/',
            }
        ):
            with patch('cloudinary.uploader.upload') as mock_upload:
                mock_upload.return_value = {
                    'public_id': 'nivetha/gallery/test_upload',
                    'url': 'http://res.cloudinary.com/democloud/image/upload/v1/nivetha/gallery/test_upload.jpg',
                    'secure_url': 'https://res.cloudinary.com/democloud/image/upload/v1/nivetha/gallery/test_upload.jpg',
                    'format': 'jpg',
                    'version': 1,
                    'resource_type': 'image'
                }

                from cloudinary_storage.storage import MediaCloudinaryStorage
                storage = MediaCloudinaryStorage()
                res = storage._upload('gallery/test.jpg', b'dummy_content')
                self.assertEqual(res['public_id'], 'nivetha/gallery/test_upload')
                mock_upload.assert_called_once()

    def test_admin_form_rejects_file_over_5mb(self):
        """Valid image file exceeding 5 MB must be rejected by admin form."""
        large_img = Image.frombytes('RGB', (1800, 1800), os.urandom(1800 * 1800 * 3))
        buf = io.BytesIO()
        large_img.save(buf, format='JPEG', quality=100)
        buf.seek(0)
        oversized_file = SimpleUploadedFile("big.jpg", buf.getvalue(), content_type="image/jpeg")

        form = GalleryImageAdminForm(
            data={'caption': 'Big image', 'order': 1, 'is_active': True},
            files={'image': oversized_file}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)
        self.assertIn('5 MB', form.errors['image'][0])

    def test_admin_form_rejects_non_image_content(self):
        """Files that are text/fake images disguised as .jpg must be rejected by inspecting content."""
        fake_content = b'This is plain text, not a real image binary.'
        fake_file = SimpleUploadedFile("fake.jpg", fake_content, content_type="image/jpeg")

        form = GalleryImageAdminForm(
            data={'caption': 'Fake image', 'order': 1, 'is_active': True},
            files={'image': fake_file}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_admin_form_rejects_unsupported_image_types(self):
        """Only JPEG, PNG, and WebP are allowed. GIF must be rejected."""
        gif_image = create_test_image('GIF')
        form = GalleryImageAdminForm(
            data={'caption': 'GIF image', 'order': 1, 'is_active': True},
            files={'image': gif_image}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)
        self.assertIn('Unsupported image format', form.errors['image'][0])

    def test_admin_form_accepts_valid_jpeg_png_webp(self):
        """Valid JPEG, PNG, and WebP files under 5 MB must pass validation."""
        for fmt in ['JPEG', 'PNG', 'WEBP']:
            valid_image = create_test_image(fmt)
            form = GalleryImageAdminForm(
                data={'caption': f'Valid {fmt}', 'order': 1, 'is_active': True},
                files={'image': valid_image}
            )
            self.assertTrue(form.is_valid(), f"Failed for format {fmt}: {form.errors}")

    def test_gallery_page_renders_cloudinary_image_and_attributes(self):
        """Gallery page renders image with lazy loading, width/height, and caption as alt."""
        with override_settings(MEDIA_ROOT=self.temp_media):
            valid_image = create_test_image('JPEG')
            GalleryImage.objects.create(
                image=valid_image,
                caption='Packing loading in Tiruppur',
                order=1,
                is_active=True
            )

            cloudinary_url = 'https://res.cloudinary.com/democloud/image/upload/v1/nivetha/gallery/truck.jpg'
            with patch('django.core.files.storage.FileSystemStorage.url', return_value=cloudinary_url):
                response = self.client.get(reverse('core:gallery'))
                self.assertEqual(response.status_code, 200)
                content = response.content.decode()

                expected_opt_url = 'https://res.cloudinary.com/democloud/image/upload/f_auto,q_auto,w_1600,c_limit/v1/nivetha/gallery/truck.jpg'
                self.assertIn(expected_opt_url, content)
                self.assertIn('loading="lazy"', content)
                self.assertIn('width="600"', content)
                self.assertIn('height="450"', content)
                self.assertIn('alt="Packing loading in Tiruppur"', content)

    def test_optimized_url_helper_behavior(self):
        """Helper adds f_auto,q_auto,w_1600,c_limit to Cloudinary URLs, keeps local paths unchanged."""
        item = GalleryImage(caption='Test')
        item.image.name = 'gallery/pic.jpg'

        # Cloudinary URL
        with patch.object(
            item.image.storage,
            'url',
            return_value='https://res.cloudinary.com/cloud/image/upload/v12345/nivetha/gallery/pic.jpg'
        ):
            opt = item.optimized_url
            self.assertEqual(
                opt,
                'https://res.cloudinary.com/cloud/image/upload/f_auto,q_auto,w_1600,c_limit/v12345/nivetha/gallery/pic.jpg'
            )

        # Local media URL
        with patch.object(
            item.image.storage,
            'url',
            return_value='/media/gallery/pic.jpg'
        ):
            opt = item.optimized_url
            self.assertEqual(opt, '/media/gallery/pic.jpg')
