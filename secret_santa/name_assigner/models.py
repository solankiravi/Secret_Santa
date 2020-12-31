from django.db import models
from django.core.validators import FileExtensionValidator
# Create your models here.

def validate_file_extension(value):
    import os
    from django.core.exceptions import ValidationError
    ext = os.path.splitext(value.name)[1]  # [0] returns path+filename
    valid_extensions = ['.xlsx', '.xls']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Unsupported file extension.')

class Team_Details(models.Model):
    name = models.CharField(max_length=200)
    child_details = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to=  "files",
                            validators=[validate_file_extension])

    def __str__(self):
        return self.name