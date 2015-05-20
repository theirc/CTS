from django.contrib import admin
from ona.models import FormSubmission


admin.site.register(
    FormSubmission,
    list_display=['pk', 'form_id', 'uuid']
)
