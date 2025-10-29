from rest_framework import serializers
from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    # Explicitly define entities to safely serialize nested JSON data
    entities = serializers.JSONField(required=False)

    class Meta:
        model = Document
        fields = [
            'id',
            'file_name',
            's3_key',
            'status',
            'extracted_text',
            'entities',
            'uploaded_at',
        ]
