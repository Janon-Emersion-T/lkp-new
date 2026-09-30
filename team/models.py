from django.db import models


class TeamMember(models.Model):
    full_name = models.CharField(max_length=150)
    profile_photo = models.ImageField(upload_to="team/")
    designation = models.CharField(max_length=150)
    department = models.CharField(max_length=100)
    bio = models.TextField()
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    joining_date = models.DateField()

    class Meta:
        ordering = ["-is_featured", "full_name"]
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"

    def __str__(self):
        return self.full_name
