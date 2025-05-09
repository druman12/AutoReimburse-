# Generated by Django 5.2 on 2025-05-07 06:35

import cloudinary.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('User', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', cloudinary.models.CloudinaryField(blank=True, help_text='Upload a Expense receipt image (optional).', max_length=255, null=True, verbose_name='file')),
                ('file_type', models.CharField(max_length=50)),
                ('file_size', models.IntegerField()),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ExpenseCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category_name', models.CharField(max_length=100)),
                ('description', models.TextField(blank=True, null=True)),
                ('budget_limit', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=15)),
                ('expense_date', models.DateField()),
                ('description', models.TextField(blank=True, null=True)),
                ('submission_date', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')], default='Pending', max_length=10)),
                ('rejection_reason', models.TextField(blank=True, null=True)),
                ('merchant_name', models.CharField(blank=True, max_length=100, null=True)),
                ('merchant_location', models.CharField(blank=True, max_length=255, null=True)),
                ('payment_method', models.CharField(choices=[('Cash', 'Cash'), ('CompanyCard', 'CompanyCard'), ('PersonalCard', 'PersonalCard'), ('UPI', 'UPI')], default='Cash', max_length=50)),
                ('is_billable', models.BooleanField(default=False)),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='User.client')),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Expense.document')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='User.employee')),
                ('project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='User.project')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Expense.expensecategory')),
            ],
        ),
        migrations.CreateModel(
            name='MLExtractionResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('processed_at', models.DateTimeField(auto_now_add=True)),
                ('extracted_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=15, null=True)),
                ('extracted_date', models.DateField(blank=True, null=True)),
                ('extracted_merchant', models.CharField(blank=True, max_length=100, null=True)),
                ('confidence_score', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Expense.document')),
                ('expense', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Expense.expense')),
                ('extracted_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Expense.expensecategory')),
            ],
        ),
    ]
