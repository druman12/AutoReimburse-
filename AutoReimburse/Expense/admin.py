from django.contrib import admin
from django.utils.html import format_html
from .models import Expense , ExpenseCategory , Document, MLExtractionResult
# Register your models here.
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('file', 'preview_or_link', 'file_type', 'file_size', 'uploaded_at')

    def preview_or_link(self, obj):
        if obj.file:
            # Check file extension
            ext = str(obj.file.url).split('.')[-1].lower()
            if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']:
                return format_html('<img src="{}" width="100" height="100" />', obj.file.url)
            elif ext == 'pdf':
                return format_html('<a href="{}" target="_blank">Open PDF</a>', obj.file.url)
            else:
                return format_html('<a href="{}" target="_blank">Download File</a>', obj.file.url)
        return "-"
    preview_or_link.short_description = "Preview / Link"

admin.site.register(Document, DocumentAdmin)
admin.site.register(ExpenseCategory)
admin.site.register(Expense)
admin.site.register(MLExtractionResult)