from .models import CareerApplication


def can_access_hr_file(user, file_url, allowed):
    """
    Return True when the requested file belongs to an HR record
    that the current user is permitted to access.
    """
    if not allowed(user, CareerApplication):
        return False

    return CareerApplication.objects.filter(
        resume_url=file_url
    ).exists()
