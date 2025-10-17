from django.db import models

class Document(models.Model):
    file_name = models.CharField(max_length=255)
    s3_key = models.CharField(max_length=500)  # thoda bada rakha, optional
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)
    entities = models.JSONField(blank=True, null=True)  # JSON structured data
    status = models.CharField(max_length=50, default="processing")  # uploaded/processing/done/failed

    def __str__(self):
        return self.file_name
