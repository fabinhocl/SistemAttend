# Django Implementation Reference

This file provides the equivalent Django / Django REST Framework (DRF) code for the EduControl backend.

## Models (models.py)

```python
from django.db import models
from django.contrib.auth.models import User

class Tenant(models.Model):
    name = models.CharField(max_length=255)
    owner = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Student(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='students')
    name = models.CharField(max_length=255)
    cpf = models.CharField(max_length=14, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    responsible_name = models.CharField(max_length=255, blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    due_day = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Package(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='packages')
    name = models.CharField(max_length=255)
    num_classes = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    validity_days = models.IntegerField(null=True, blank=True)
    category = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name

class Contract(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('finished', 'Finished'),
        ('cancelled', 'Cancelled'),
    ]
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='contracts')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    start_date = models.DateField()
    preferred_instructor = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"{self.student.name} - {self.package.name}"
```

## Serializers (serializers.py)

```python
from rest_framework import serializers
from .models import Student, Package, Contract

class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = '__all__'

class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'

class ContractSerializer(serializers.ModelSerializer):
    student_name = serializers.ReadOnlyField(source='student.name')
    package_name = serializers.ReadOnlyField(source='package.name')
    
    class Meta:
        model = Contract
        fields = '__all__'
```

## ViewSets (views.py)

```python
from rest_framework import viewsets
from .models import Student, Package, Contract
from .serializers import StudentSerializer, PackageSerializer, ContractSerializer

class TenantFilteredViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        # Simulating multi-tenancy filtering
        tenant_id = self.request.headers.get('x-tenant-id')
        return self.queryset.filter(tenant_id=tenant_id)

class StudentViewSet(TenantFilteredViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer

class PackageViewSet(TenantFilteredViewSet):
    queryset = Package.objects.all()
    serializer_class = PackageSerializer

class ContractViewSet(TenantFilteredViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
```
