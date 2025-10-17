from rest_framework import serializers
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        # Add uploaded_at and ensure entities is included
        fields = ['id', 'file_name', 's3_key', 'status', 'extracted_text', 'entities', 'uploaded_at']
