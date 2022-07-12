from django.core.validators import MinValueValidator
from django.db import models


class Employee(models.Model):
    branch = models.CharField(max_length=100)
    full_name = models.CharField(max_length=150)
    position = models.CharField(max_length=100)
    birth_date = models.DateField()
    internal_id = models.PositiveIntegerField(unique=True)
    employment_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

