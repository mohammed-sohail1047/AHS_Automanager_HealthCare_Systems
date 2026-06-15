from django.db import models
from django.contrib.auth.hashers import make_password, check_password
import uuid
from datetime import timedelta
from django.utils import timezone

# Create your models here.


class AdminType(models.Model):
    Id= models.IntegerField(primary_key=True)
    Name = models.CharField(max_length=100)
    Description = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.Name} ({self.Id})"
    class Meta:
        db_table = 'AdminType'

class AdminLogin(models.Model):
    Id = models.IntegerField(primary_key=True)
    Name = models.CharField(max_length=100)
    Gender = models.CharField(max_length=10)
    Password = models.CharField(max_length=128)
    Phone = models.CharField(max_length=15)
    Email = models.EmailField()
    Address = models.CharField(max_length=100)
    AdminType = models.ForeignKey(AdminType, on_delete=models.CASCADE, db_column='AdminType')
    Status = models.BooleanField(default=False)
    # Createdby = models.CharField(max_length=100, null=True, blank=True)
    # CreatedOn = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.Name} ({self.Id})"
    
    def save(self, *args, **kwargs):
        # Hash password if it hasn't been hashed already
        if self.Password and not self.Password.startswith('pbkdf2_sha256$'):
            self.Password = make_password(self.Password)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        """Verify the password matches the hashed password"""
        return check_password(raw_password, self.Password)
    
    class Meta:
        db_table = 'AdminLogin'

class Department(models.Model):
    DeptNo = models.AutoField(primary_key=True)
    Dname = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.DeptNo} {self.Dname}"
    
    class Meta:
        db_table = 'Department'

class Employee(models.Model):
    EmpID = models.IntegerField(primary_key=True)
    Ename = models.CharField(max_length=50)
    Gender = models.CharField(max_length=10)
    Password = models.CharField(max_length=128)
    Phone = models.CharField(max_length=15)
    Email = models.EmailField()
    Salary = models.FloatField()
    Address = models.CharField(max_length=100)
    IsActive = models.BooleanField(default=True)
    IsAdmin = models.BooleanField(default=False)
    IsLoggedIn = models.BooleanField(default=False)
    DeptNo = models.ForeignKey(Department, on_delete=models.CASCADE, db_column='DeptNo')

    def __str__(self):
        return f"{self.EmpID} {self.Ename}"
    
    def save(self, *args, **kwargs):
        # Hash password if it hasn't been hashed already
        if self.Password and not self.Password.startswith('pbkdf2_sha256$'):
            self.Password = make_password(self.Password)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        """Verify the password matches the hashed password"""
        return check_password(raw_password, self.Password)
    
    class Meta:
        db_table = 'Employee'

class Doctor(models.Model):
    DocID = models.IntegerField(primary_key=True)
    Dname = models.CharField(max_length=50)
    Specialization = models.CharField(max_length=100)
    Phone = models.CharField(max_length=15)
    Email = models.EmailField()
    Password = models.CharField(max_length=128, null=True, blank=True)
    Status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.DocID} {self.Dname}"

    def save(self, *args, **kwargs):
        if self.Password and not self.Password.startswith('pbkdf2_sha256$'):
            self.Password = make_password(self.Password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return bool(self.Password) and check_password(raw_password, self.Password)
    
    class Meta:
        db_table = 'Doctor'

class Receptionist(models.Model):
    RecID = models.IntegerField(primary_key=True)
    Rname = models.CharField(max_length=50)
    Phone = models.CharField(max_length=15)
    Email = models.EmailField()
    Password = models.CharField(max_length=128, null=True, blank=True)
    Status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.RecID} {self.Rname}"

    def save(self, *args, **kwargs):
        if self.Password and not self.Password.startswith('pbkdf2_sha256$'):
            self.Password = make_password(self.Password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return bool(self.Password) and check_password(raw_password, self.Password)
    
    class Meta:
        db_table = 'Receptionist'

class Helper(models.Model):
    HelperID = models.IntegerField(primary_key=True)
    Hname = models.CharField(max_length=50)
    Phone = models.CharField(max_length=15)
    Email = models.EmailField()
    Password = models.CharField(max_length=128, null=True, blank=True)
    Status = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.HelperID} {self.Hname}"

    def save(self, *args, **kwargs):
        if self.Password and not self.Password.startswith('pbkdf2_sha256$'):
            self.Password = make_password(self.Password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return bool(self.Password) and check_password(raw_password, self.Password)
    
    class Meta:
        db_table = 'Helper'

class Patient(models.Model):
    PatientID = models.IntegerField(primary_key=True)
    Pname = models.CharField(max_length=50)
    Age = models.IntegerField()
    Gender = models.CharField(max_length=10)
    Phone = models.CharField(max_length=15)
    Email = models.EmailField()
    ReceptionistID = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column='ReceptionistID', related_name='receptionist_patients')
    DoctorID = models.ForeignKey(Doctor, on_delete=models.CASCADE, db_column='DoctorID')
    HelperID = models.ForeignKey(Employee, on_delete=models.CASCADE, db_column='HelperID', related_name='helper_patients')
    Prescription = models.CharField(max_length=250)
    EntryDateandTime = models.DateTimeField(auto_now_add=True)
    ExitDateandTime = models.DateTimeField(null=True, blank=True)
    IsAdmitted = models.BooleanField(default=False)
    Medication = models.CharField(max_length=250)
    Bill= models.CharField(max_length=500)

    class Meta:
        db_table = 'Patient'

class CheckLogin(models.Model):
    email = models.EmailField()
    username = models.CharField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=15,null=True, blank=True)
    # additional profile fields
    address = models.CharField(max_length=200, null=True, blank=True, db_column='Address')
    gender = models.CharField(max_length=10, null=True, blank=True, db_column='Gender')
    # avatar image
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, db_column='Avatar')
    password = models.CharField(max_length=100)
    admin_type = models.CharField(max_length=20)
    status = models.BooleanField(default=False)
    # Track who created this admin and when
    created_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='created_admins', db_column='CreatedBy')
    created_on = models.DateTimeField(auto_now_add=True, db_column='CreatedOn')

    ADMIN_TYPE_CHOICES = (
        (1, 'MAdmin'),
        (2, 'OpAdmin'),
    )

    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        # Hash password if it hasn't been hashed already
        if self.password and not self.password.startswith('pbkdf2_sha256$'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)
    
    def check_password(self, raw_password):
        """Verify the password matches the hashed password"""
        return check_password(raw_password, self.password)
    
    class Meta:
        db_table = 'CheckLogin'


class PasswordResetToken(models.Model):
    """Model to store password reset tokens"""
    email = models.EmailField()
    token = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Reset token for {self.email}"

    def save(self, *args, **kwargs):
        # Set expiration to 24 hours from now if not already set
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_valid(self):
        """Check if token is still valid"""
        return not self.is_used and timezone.now() < self.expires_at

    class Meta:
        db_table = 'PasswordResetToken'

