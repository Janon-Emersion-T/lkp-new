from pathlib import Path
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import transaction
from django.shortcuts import render
from django.views.decorators.http import require_POST

from pages.models import Enquiry

from .models import CareerApplication


@require_POST
def apply_for_job(request):
    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()

    application = CareerApplication(
        name=name,
        email=email,
        phone=request.POST.get("phone", ""),
        position=request.POST.get("position", "") or "General application",
        message=request.POST.get("message", ""),
    )

    upload = request.FILES.get("resume")

    try:
        application.full_clean()

        if upload:
            extension = Path(upload.name).suffix.lower()

            if extension not in [".pdf", ".docx"] or upload.size > 5 * 1024 * 1024:
                raise ValidationError(
                    "Upload a PDF or DOCX no larger than 5 MB."
                )

            path = default_storage.save(
                f"dashboard/resumes/{uuid4().hex}{extension}",
                upload,
            )

            application.resume_url = f"/dashboard/files/{path}"

        with transaction.atomic():
            application.save()

            Enquiry.objects.create(
                source="career",
                name=name,
                email=email,
                phone=application.phone,
                subject=application.position,
                message=application.message or "Career application",
            )

    except ValidationError as error:
        return render(
            request,
            "site/submission.html",
            {
                "title": "Application needs attention",
                "message": "; ".join(error.messages),
            },
            status=400,
        )

    return render(
        request,
        "site/submission.html",
        {
            "title": "Application received",
            "message": "Thank you. Our team will review your application.",
        },
    )
