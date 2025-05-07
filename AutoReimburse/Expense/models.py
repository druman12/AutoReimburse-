from django.db import models
from User.models import Employee , Project , Client
from cloudinary.models import CloudinaryField

class ExpenseCategory(models.Model):
    category_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    budget_limit = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.category_name
    
class Document(models.Model):
    file = CloudinaryField('file',
        folder="images/Docs/Receipts",
        null=True,
        blank=True,
        help_text="Upload a Expense receipt image (optional).")  
    file_type = models.CharField(max_length=50)
    file_size = models.IntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.public_id if self.file else self.file_name or "No File"
    
class Expense(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    PAYMENT_CHOICES = [
        ('Cash', 'Cash'),
        ('CompanyCard', 'CompanyCard'),
        ('PersonalCard', 'PersonalCard'),
        ('UPI','UPI'),
    ]

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=15, decimal_places=2 , blank=True , null=True)
    expense_date = models.DateField(null=True , blank=True)
    description = models.TextField(blank=True, null=True)
    submission_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    rejection_reason = models.TextField(blank=True, null=True)
    merchant_name = models.CharField(max_length=100, blank=True, null=True)
    merchant_location = models.CharField(max_length=255, blank=True, null=True)
    payment_method = models.CharField(max_length=50,choices=PAYMENT_CHOICES,default='Cash')
    is_billable = models.BooleanField(default=False)
    extracted = models.BooleanField(default=False) 

    def save(self, *args, **kwargs):
        if self.payment_method in ['UPI', 'PersonalCard', 'Cash']:
            self.is_billable = True
        else:
            self.is_billable = False
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Expense #{self.id} - {self.employee}"


class MLExtractionResult(models.Model):
    expense = models.ForeignKey(Expense, on_delete=models.CASCADE)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
    processed_at = models.DateTimeField(auto_now_add=True)
    extracted_amount = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    extracted_date = models.DateField(blank=True, null=True)
    extracted_merchant = models.CharField(max_length=100, blank=True, null=True)
    extracted_merchant_location = models.CharField(max_length=150, blank=True, null=True)
    extracted_category = models.ForeignKey(ExpenseCategory, on_delete=models.SET_NULL, null=True, blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    def __str__(self):
        return f"Extraction for Expense #{self.expense.id}"