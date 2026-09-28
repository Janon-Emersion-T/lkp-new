import os
from pathlib import Path
import subprocess
from uuid import uuid4

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .access import audit, staff_required
from .models import BackupRecord


@staff_required
@require_POST
def create_backup(request):
    if not request.user.is_superuser:
        raise PermissionDenied
    record = BackupRecord.objects.create(label=f'Database backup {timezone.now():%Y-%m-%d %H:%M}')
    database = settings.DATABASES['default']
    directory = Path(settings.MEDIA_ROOT) / 'dashboard' / 'backups'
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    filename = directory / f'{uuid4().hex}.dump'
    env = {**os.environ, 'PGPASSWORD': database.get('PASSWORD', '')}
    try:
        subprocess.run(['pg_dump', '--format=custom', '--no-owner', '--host', database['HOST'], '--port', str(database['PORT']), '--username', database['USER'], '--file', str(filename), database['NAME']], env=env, capture_output=True, check=True, timeout=120)
        filename.chmod(0o600)
        record.status = 'complete'
        record.file_url = f'/dashboard/files/dashboard/backups/{filename.name}'
        record.notes = 'PostgreSQL custom-format backup. Uploaded media is stored separately.'
        messages.success(request, 'Database backup created.')
    except (OSError, subprocess.SubprocessError):
        filename.unlink(missing_ok=True)
        record.status = 'failed'
        record.notes = 'Database backup failed. Check PostgreSQL connectivity and pg_dump availability.'
        messages.error(request, record.notes)
    record.save()
    audit(request.user, 'Database backup', record, status=record.status)
    return redirect('dashboard_detail', resource='backups', pk=record.pk)
