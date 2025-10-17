import time
import uuid
import boto3
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UploadPDFForm
from .models import Document
#from .utils import parse_pdf_by_headings  # updated utils function
from .utils import extract_entities

from .serializers import DocumentSerializer

# DRF imports
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

# ===============================
# AWS Clients Setup
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

# ===============================
# PDF Processing Function
# ===============================
def process_pdf_s3(doc):
    """
    Runs Textract text detection on the uploaded PDF (stored in S3),
    extracts text, and uses regex (utils.extract_entities)
    to structure the extracted entities.
    """
    s3_key = doc.s3_key
    bucket = settings.AWS_S3_BUCKET

    # Step 1: Check if file exists in S3
    try:
        s3.head_object(Bucket=bucket, Key=s3_key)
    except s3.exceptions.ClientError:
        doc.status = "failed"
        doc.extracted_text = "S3 object not found."
        doc.save()
        return doc

    # Step 2: Start Textract job
    start_job = textract.start_document_text_detection(
        DocumentLocation={'S3Object': {'Bucket': bucket, 'Name': s3_key}}
    )
    job_id = start_job["JobId"]
    print(f"Textract job started: {job_id}")

    # Step 3: Poll Textract status
    while True:
        time.sleep(5)
        resp = textract.get_document_text_detection(JobId=job_id)
        status_ = resp["JobStatus"]
        print(f"Textract status: {status_}")
        if status_ in ["SUCCEEDED", "FAILED"]:
            break

    # Step 4: Process results
    if status_ == "SUCCEEDED":
        blocks = resp["Blocks"]
        next_token = resp.get("NextToken")

        # Paginate through all results
        while next_token:
            next_page = textract.get_document_text_detection(JobId=job_id, NextToken=next_token)
            blocks.extend(next_page["Blocks"])
            next_token = next_page.get("NextToken")

        # Combine all detected lines
        lines = [b["Text"] for b in blocks if b["BlockType"] == "LINE"]
        extracted_text = "\n".join(lines)
        doc.extracted_text = extracted_text

        # Step 5: Parse structured entities
        if extracted_text.strip():
            entities = extract_entities(extracted_text)
            doc.entities = entities

        doc.status = "done"
        doc.save()
        print(f"✅ Textract + Regex parsing completed for: {s3_key}")

    else:
        doc.status = "failed"
        doc.extracted_text = "Textract failed to process this document."
        doc.save()
        print(f"❌ Textract failed for {s3_key}")

    return doc


# ===============================
# 1️⃣ Web Upload View
# ===============================
def upload_pdf(request):
    """
    Web-based upload view for OCR + Entity extraction.
    Uploads file → S3 → Textract → utils regex parsing → Save to DB
    """
    if request.method == "POST":
        form = UploadPDFForm(request.POST, request.FILES)
        if form.is_valid():
            pdf = form.cleaned_data["pdf_file"]
            file_name = f"{uuid.uuid4().hex}_{pdf.name}"
            s3_key = f"uploads/{file_name}"

            # Upload PDF to S3
            s3.upload_fileobj(
                pdf,
                settings.AWS_S3_BUCKET,
                s3_key,
                ExtraArgs={"ContentType": "application/pdf"},
            )

            # Save DB record
            doc = Document.objects.create(
                file_name=file_name, s3_key=s3_key, status="processing"
            )

            # Run Textract + regex parsing
            process_pdf_s3(doc)

            return redirect("result", pk=doc.pk)
    else:
        form = UploadPDFForm()

    return render(request, "upload.html", {"form": form})


# ===============================
# 2️⃣ API Upload + Extraction Endpoint
# ===============================
@api_view(["POST"])
@parser_classes([MultiPartParser, FormParser])
def pdf_extraction_api(request):
    """
    REST API endpoint: Upload PDF → S3 → Textract → regex parsing → return JSON
    """
    if "file" not in request.FILES:
        return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

    pdf = request.FILES["file"]
    file_name = f"{uuid.uuid4().hex}_{pdf.name}"
    s3_key = f"uploads/{file_name}"

    # Upload to S3
    s3.upload_fileobj(
        pdf,
        settings.AWS_S3_BUCKET,
        s3_key,
        ExtraArgs={"ContentType": "application/pdf"},
    )

    # Create Document record
    doc = Document.objects.create(file_name=file_name, s3_key=s3_key, status="processing")

    # Process PDF (Textract + utils)
    processed_doc = process_pdf_s3(doc)

    # Return serialized response
    serializer = DocumentSerializer(processed_doc)
    return Response(serializer.data, status=status.HTTP_200_OK)


# ===============================
# 3️⃣ Result View
# ===============================
def result_view(request, pk):
    """
    Displays extraction result after upload.
    """
    doc = get_object_or_404(Document, pk=pk)
    return render(request, "result.html", {"doc": doc})
