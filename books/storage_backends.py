from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings

class PublicMediaStorage(S3Boto3Storage):
    bucket_name = settings.SUPABASE_PUBLIC_BUCKET
    custom_domain = f"{settings.SUPABASE_URL.replace('https://', '')}/storage/v1/object/public/{settings.SUPABASE_PUBLIC_BUCKET}"