from django.db import models

class Document(models.Model):
    file_name = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    s3_key = models.CharField(max_length=255)
    extracted_text = models.TextField(blank=True, null=True)
    entities = models.JSONField(blank=True, null=True)
    status = models.CharField(max_length=50, default="uploaded")

    def __str__(self):
        return self.file_name
