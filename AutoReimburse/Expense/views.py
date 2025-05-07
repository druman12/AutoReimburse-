from django.shortcuts import render, redirect
from .models import Expense, ExpenseCategory, Project, Client, Document
from User.models import Employee , User # or however you're handling logged-in users

def add_expense(request):
    if request.method == 'POST':
        # Extract values from POST request
        employee = Employee.objects.get(user=request.user)  # Adjust if needed
        category_id = request.POST.get('category')
        project_id = request.POST.get('project')
        client_id = request.POST.get('client')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        payment_method = request.POST.get('payment_method')

        uploaded_file = request.FILES.get('document')

        # Save document using Cloudinary for image storage
        document = Document.objects.create(
            file=uploaded_file,  # CloudinaryField will handle this
            file_type=uploaded_file.content_type,
            file_size=uploaded_file.size,
        )

        # Save expense
        category = ExpenseCategory.objects.get(id=category_id)
        project = Project.objects.get(id=project_id) if project_id else None
        client = Client.objects.get(id=client_id) if client_id else None

        expense = Expense.objects.create(
            employee=employee,
            category=category,
            project=project,
            client=client,
            document=document,
            amount=amount,
            expense_date=None,  # to be filled by ML later
            description=description,
            payment_method=payment_method,
            
        )

        # Trigger ML processing (optional step)
        # process_document(expense)

        return redirect('success_page')  # Or wherever you want to redirect

    # GET request — show form
    employee = User.objects.filter(user_type='Employee')
    categories = ExpenseCategory.objects.filter(is_active=True)
    projects = Project.objects.all()
    clients = Client.objects.all()

    return render(request, 'expense_form.html', {
        'employee': employee,
        'categories': categories,
        'projects': projects,
        'clients': clients,
    })

import pytesseract
import tempfile
import requests
from PIL import Image
import re
from django.http import JsonResponse
from .models import Expense, MLExtractionResult


def extract_merchant_name(ocr_text):
    lines = [line.strip() for line in ocr_text.strip().split('\n') if line.strip()]
    common_noise = ['invoice', 'receipt', 'date', 'tax', 'gst', 'total', 'amount', 'no:', 'qty', 'cashier', 'bill']

    # Check top 8 lines for potential merchant names
    candidates = []
    for line in lines[:8]:
        lower = line.lower()
        if 4 < len(line) < 50 and not any(word in lower for word in common_noise):
            if re.match(r'^[A-Za-z0-9 &().,\-\'"]+$', line):  # Ensure it's mostly readable text
                candidates.append(line)

    # Prefer lines in Title Case (likely a business name)
    title_case_candidates = [line for line in candidates if line == line.title()]

    if title_case_candidates:
        return title_case_candidates[0]

    if candidates:
        return candidates[0]

    return lines[0] if lines else None


import re

def extract_amount(ocr_text):
    total_patterns = [
        r'\bTotal\s*[:\-]?\s*[£$€₹]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b',
        r'\bTOTAL\s*[:\-]?\s*[£$€₹]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b',
        r'\btotal\s*[:\-]?\s*[£$€₹]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b',
        r'\bAmount\s+(?:Due|Payable|To\s+Pay)?\s*[:\-]?\s*[£$€₹]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b',
        r'\bGrand\s+Total\s*[:\-]?\s*[£$€₹]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b',
        r'\bSubtotal\s*[:\-]?\s*[£$€₹]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b',
        r'\bBalance\s+Due\s*[:\-]?\s*[£$€₹]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b',
        r'\bTotal\s+Amount\s*[:\-]?\s*[£$€₹]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b'
    ]

    # First try total-specific patterns
    for pattern in total_patterns:
        match = re.search(pattern, ocr_text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except:
                continue

    # Fallback: get the last currency-like number
    fallback_matches = re.findall(r'\b[£$€₹]?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2}))\b', ocr_text)
    if fallback_matches:
        try:
            return float(fallback_matches[-1].replace(',', ''))
        except:
            pass

    return None


def extract_date(ocr_text):
    date_patterns = [
        r'\b\d{4}[-/]\d{2}[-/]\d{2}\b',
        r'\b\d{2}[-/]\d{2}[-/]\d{4}\b',
        r'\b\d{2}[.]\d{2}[.]\d{4}\b',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[.]?\s+\d{1,2},\s+\d{4}\b',
        r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',
        r'\b\d{1,2}[ ]?[A-Za-z]{3,9}[ ]?\d{4}\b',
        r'\b\d{2}-[A-Za-z]{3}-\d{4}\b'
    ]
    for pattern in date_patterns:
        match = re.search(pattern, ocr_text)
        if match:
            from datetime import datetime
            try:
                return datetime.strptime(match.group(1), "%d/%m/%Y").date()
            except:
                try:
                    return datetime.strptime(match.group(1), "%Y-%m-%d").date()
                except:
                    try:
                        return datetime.strptime(match.group(1), "%d-%m-%Y").date()
                    except:
                        pass
    return None

from .models import ExpenseCategory  # Import your category model

CATEGORY_KEYWORDS = {
    'Food': ['food', 'restaurant', 'snack', 'lunch', 'dinner', 'meal'],
    'Travelling': ['travel', 'taxi', 'flight', 'bus', 'cab', 'uber', 'ola'],
    'Hotel': ['hotel', 'stay', 'inn', 'lodging', 'accommodation', 'resort']
}

def extract_category_from_text(ocr_text):
    text_lower = ocr_text.lower()
    best_match = None
    highest_match_count = 0

    for category, keywords in CATEGORY_KEYWORDS.items():
        count = sum(keyword in text_lower for keyword in keywords)
        if count > highest_match_count:
            highest_match_count = count
            best_match = category

    if best_match:
        try:
            return ExpenseCategory.objects.get(category_name__iexact=best_match)
        except ExpenseCategory.DoesNotExist:
            return None

    return None



def extract_location(text):
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    address_pattern = re.compile(r'\d{1,5}\s+\w+(?:\s+\w+)*[,.\- ]+(?:road|street|rd|st|block|area|city|town|india|usa|uk)', re.IGNORECASE)

    for line in lines:
        if address_pattern.search(line):
            return line

    # Try combining adjacent lines
    for i in range(len(lines) - 1):
        combined = lines[i] + ' ' + lines[i + 1]
        if address_pattern.search(combined):
            return combined

    return None


def extract_from_expense_document(request, expense_id):
    try:
        expense = Expense.objects.get(id=expense_id)
        document_url = expense.document.file.url

        response = requests.get(document_url)
        if response.status_code != 200:
            return JsonResponse({'error': 'Could not download document image'}, status=400)

        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            temp_file.write(response.content)
            temp_path = temp_file.name

        image = Image.open(temp_path)
        ocr_text = pytesseract.image_to_string(image)

        # Extract fields from OCR text
        amount = extract_amount(ocr_text)
        merchant = extract_merchant_name(ocr_text)
        date = extract_date(ocr_text)
        extracted_category = extract_category_from_text(ocr_text)
        location = extract_location(ocr_text)  # NEW

        # Update or create MLExtractionResult
        result, created = MLExtractionResult.objects.get_or_create(
            expense=expense,
            document=expense.document,
            defaults={
                'extracted_amount': amount,
                'extracted_date': date,
                'extracted_merchant': merchant,
                'extracted_category': extracted_category,
                'extracted_merchant_location': location,
            }
        )

        if not created:
            result.extracted_amount = amount
            result.extracted_date = date
            result.extracted_merchant = merchant
            result.extracted_category = extracted_category
            result.extracted_merchant_location = location
            result.save()

        # 🟢 Update Expense with non-null fields from MLExtractionResult
        updated = False
        if result.extracted_amount is not None:
            expense.amount = result.extracted_amount
            updated = True
        if result.extracted_date is not None:
            expense.expense_date = result.extracted_date
            updated = True
        if result.extracted_merchant:
            expense.merchant_name = result.extracted_merchant
            updated = True
        if result.extracted_merchant_location:
            expense.merchant_location = result.extracted_merchant_location
            updated = True
        if result.extracted_category:
            expense.category = result.extracted_category
            updated = True

        if updated:
            expense.extracted = True
            expense.save()

        return JsonResponse({
            'status': 'success',
            'created': created,
            'extracted_amount': amount,
            'extracted_date': date,
            'extracted_merchant': merchant,
            'extracted_category': str(extracted_category) if extracted_category else None,
            'merchant_location': location,
        })

    except Expense.DoesNotExist:
        return JsonResponse({'error': 'Expense not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from Expense.models import Expense
import json
from datetime import datetime


@csrf_exempt
def expense_api(request, expense_id=None):
    if request.method == 'GET':
        if expense_id:
            try:
                expense = Expense.objects.get(id=expense_id)
                data = {
                    'id': expense.id,
                    'employee_id': expense.employee_id,
                    'category_id': expense.category_id,
                    'project_id': expense.project_id,
                    'client_id': expense.client_id,
                    'document_id': expense.document_id,
                    'amount': float(expense.amount),
                    'expense_date': str(expense.expense_date),
                    'description': expense.description,
                    'submission_date': str(expense.submission_date),
                    'status': expense.status,
                    'rejection_reason': expense.rejection_reason,
                    'merchant_name': expense.merchant_name,
                    'merchant_location': expense.merchant_location,
                    'payment_method': expense.payment_method,
                    'is_billable': expense.is_billable,
                }
                return JsonResponse(data, status=200)
            except Expense.DoesNotExist:
                return JsonResponse({"error": "Expense not found"}, status=404)

        else:
            expenses = Expense.objects.all().values()
            return JsonResponse(list(expenses), safe=False)

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            expense = Expense.objects.create(
                employee_id=data['employee_id'],
                category_id=data['category_id'],
                project_id=data.get('project_id'),
                client_id=data.get('client_id'),
                document_id=data['document_id'],
                amount=data['amount'],
                expense_date=data.get('expense_date'),
                description=data.get('description'),
                status=data.get('status', 'Pending'),
                rejection_reason=data.get('rejection_reason'),
                merchant_name=data.get('merchant_name'),
                merchant_location=data.get('merchant_location'),
                payment_method=data.get('payment_method', 'Cash'),
            )

            return JsonResponse({"message": "Expense created", "id": expense.id}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == 'PUT':
        if not expense_id:
            return JsonResponse({"error": "Expense ID required for update"}, status=400)
        try:
            data = json.loads(request.body)
            expense = Expense.objects.get(id=expense_id)

            def safe_update(field_name):
                if field_name in data and data[field_name] is not None:
                    setattr(expense, field_name, data[field_name])

            # Update only provided, non-null fields
            safe_update('employee_id')
            safe_update('category_id')
            safe_update('project_id')
            safe_update('client_id')
            safe_update('document_id')
            safe_update('amount')
            safe_update('expense_date')
            safe_update('description')
            safe_update('status')
            safe_update('rejection_reason')
            safe_update('merchant_name')
            safe_update('merchant_location')
            safe_update('payment_method')

            expense.save()

            return JsonResponse({"message": "Expense updated successfully"}, status=200)

        except Expense.DoesNotExist:
            return JsonResponse({"error": "Expense not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)
