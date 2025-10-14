import time
import uuid
import boto3
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UploadPDFForm
from .models import Document

# DRF imports for API
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from .serializers import DocumentSerializer

# ===============================
# AWS Clients
# ===============================
s3 = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)
textract = boto3.client(
    "textract",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)
comprehend = boto3.client(
    "comprehend",
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

# ===============================
# Common Extraction Function
# ===============================
def process_pdf_s3(doc):
    """Run Textract + Comprehend on uploaded S3 PDF and update Document model."""
    s3_key = doc.s3_key

    # ✅ Step 1: Verify S3 object exists
    try:
        s3.head_object(Bucket=settings.AWS_S3_BUCKET, Key=s3_key)
    except s3.exceptions.ClientError:
        doc.status = "failed"
        doc.extracted_text = "S3 object not found."
        doc.save()
        return doc

    # ✅ Step 2: Start Textract job
    start_job = textract.start_document_text_detection(
        DocumentLocation={'S3Object': {'Bucket': settings.AWS_S3_BUCKET, 'Name': s3_key}}
    )
    job_id = start_job['JobId']
    print(f"Textract job started: {job_id}")

    # ✅ Step 3: Poll Textract job status
    while True:
        time.sleep(5)
        resp = textract.get_document_text_detection(JobId=job_id)
        status = resp['JobStatus']
        print(f"Textract status: {status}")
        if status in ['SUCCEEDED', 'FAILED']:
            break

    # ✅ Step 4: Process results
    if status == 'SUCCEEDED':
        blocks = resp['Blocks']
        next_token = resp.get('NextToken')
        while next_token:
            next_page = textract.get_document_text_detection(JobId=job_id, NextToken=next_token)
            blocks.extend(next_page['Blocks'])
            next_token = next_page.get('NextToken')

        lines = [b['Text'] for b in blocks if b['BlockType'] == 'LINE']
        extracted_text = "\n".join(lines)
        doc.extracted_text = extracted_text

        # ✅ Step 5: Run Comprehend on extracted text
        if extracted_text.strip():
            comp = comprehend.detect_entities(Text=extracted_text[:5000], LanguageCode='en')
            doc.entities = comp['Entities']

        doc.status = "done"
        doc.save()
        print(f"Textract + Comprehend completed successfully for {s3_key}")
    else:
        doc.status = "failed"
        doc.extracted_text = "Textract failed to process this document."
        doc.save()
        print(f"Textract failed for {s3_key}")

    return doc

# ===============================
# 1️⃣ Web Form Upload View
# ===============================
def upload_pdf(request):
    if request.method == 'POST':
        form = UploadPDFForm(request.POST, request.FILES)
        if form.is_valid():
            pdf = form.cleaned_data['pdf_file']
            file_name = f"{uuid.uuid4().hex}_{pdf.name}"
            s3_key = f"uploads/{file_name}"

            # Upload PDF to S3
            s3.upload_fileobj(
                pdf,
                settings.AWS_S3_BUCKET,
                s3_key,
                ExtraArgs={'ContentType': 'application/pdf'}
            )

            # Save DB record
            doc = Document.objects.create(file_name=file_name, s3_key=s3_key, status='processing')

            # Process the PDF using Textract + Comprehend
            process_pdf_s3(doc)

            return redirect('result', pk=doc.pk)
    else:
        form = UploadPDFForm()

    return render(request, 'upload.html', {'form': form})

# ===============================
# 2️⃣ API Endpoint for PDF Extraction
# ===============================
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def pdf_extraction_api(request):
    """API endpoint: Upload PDF → S3 → Textract → Comprehend → Return JSON"""
    if 'file' not in request.FILES:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

    pdf = request.FILES['file']
    file_name = f"{uuid.uuid4().hex}_{pdf.name}"
    s3_key = f"uploads/{file_name}"

    # Upload to S3
    s3.upload_fileobj(pdf, settings.AWS_S3_BUCKET, s3_key, ExtraArgs={'ContentType': 'application/pdf'})

    # Create Document record
    doc = Document.objects.create(file_name=file_name, s3_key=s3_key, status='processing')

    # Run Textract + Comprehend
    processed_doc = process_pdf_s3(doc)

    # Serialize and return JSON response
    serializer = DocumentSerializer(processed_doc)
    return Response(serializer.data, status=status.HTTP_200_OK)

# ===============================
# 3️⃣ Result View
# ===============================
def result_view(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    return render(request, 'result.html', {'doc': doc})
