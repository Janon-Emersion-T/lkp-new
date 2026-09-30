from django import forms

from pages.forms import DashboardModelForm

from .models import TeamMember


class TeamMemberForm(DashboardModelForm):
    class Meta:
        model = TeamMember
        fields = [
            'full_name',
            'profile_photo',
            'designation',
            'department',
            'bio',
            'is_active',
            'is_featured',
            'joining_date',
        ]
        widgets = {
            'profile_photo': forms.ClearableFileInput(
                attrs={
                    'accept': 'image/jpeg,image/png,image/webp'
                }
            ),
            'bio': forms.Textarea(
                attrs={
                    'rows': 6
                }
            ),
            'joining_date': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),
        }
