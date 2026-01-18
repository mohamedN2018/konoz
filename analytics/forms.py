# analytics/forms.py
from django import forms


class AnalyticsSettingsForm(forms.Form):
    refresh_interval = forms.IntegerField(
        label='فترة التحديث التلقائي (ثانية)',
        min_value=10,
        max_value=300,
        initial=30,
        help_text='فترة تحديث البيانات التلقائي بالثواني'
    )
    
    show_realtime = forms.BooleanField(
        label='عرض الزوار الفوريين',
        initial=True,
        required=False
    )
    
    show_map = forms.BooleanField(
        label='عرض الخريطة',
        initial=True,
        required=False
    )
    
    default_period = forms.ChoiceField(
        label='الفترة الافتراضية',
        choices=[
            ('7d', 'أسبوع'),
            ('30d', 'شهر'),
            ('90d', '3 أشهر'),
            ('1y', 'سنة'),
        ],
        initial='30d'
    )
    
    anonymize_ip = forms.BooleanField(
        label='إخفاء عناوين IP',
        initial=True,
        required=False,
        help_text='إخفاء الجزء الأخير من عناوين IP لحماية خصوصية المستخدمين'
    )