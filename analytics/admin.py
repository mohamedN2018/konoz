# analytics/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Country, VisitorSession, PageView, 
    RealTimeVisitor, AnalyticsDashboard, AlertRule
)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['flag_emoji', 'name', 'code', 'visits', 'avg_time_spent_display', 'last_visit']
    list_filter = ['name']
    search_fields = ['name', 'code']
    readonly_fields = ['visits', 'total_time_spent']
    
    def avg_time_spent_display(self, obj):
        return str(obj.avg_time_spent())
    avg_time_spent_display.short_description = 'متوسط الوقت'

@admin.register(VisitorSession)
class VisitorSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id_short', 'country_flag', 'device_type', 'page_count', 
                    'duration_display', 'is_active_display', 'start_time']
    list_filter = ['device_type', 'country', 'is_active', 'start_time']
    search_fields = ['session_id', 'ip_address', 'city']
    readonly_fields = ['start_time', 'end_time']
    
    def session_id_short(self, obj):
        return str(obj.session_id)[:8] + '...'
    session_id_short.short_description = 'معرف الجلسة'
    
    def country_flag(self, obj):
        if obj.country and obj.country.flag_emoji:
            return f"{obj.country.flag_emoji} {obj.country.name}"
        return "🌐 غير معروف"
    country_flag.short_description = 'الدولة'
    
    def duration_display(self, obj):
        return str(obj.duration)
    duration_display.short_description = 'المدة'
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">●</span> نشطة')
        return format_html('<span style="color: red;">●</span> منتهية')
    is_active_display.short_description = 'الحالة'

@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ['title_short', 'session_link', 'time_spent', 'scroll_depth_display', 
                    'is_bounce_display', 'timestamp']
    list_filter = ['is_bounce', 'timestamp']
    search_fields = ['title', 'url']
    readonly_fields = ['timestamp']
    
    def title_short(self, obj):
        return (obj.title[:50] + '...') if len(obj.title) > 50 else obj.title
    title_short.short_description = 'العنوان'
    
    def session_link(self, obj):
        url = f"/admin/analytics/visitorsession/{obj.session.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.session.session_id_short())
    session_link.short_description = 'الجلسة'
    
    def scroll_depth_display(self, obj):
        return f"{obj.scroll_depth}%"
    scroll_depth_display.short_description = 'عمق التمرير'
    
    def is_bounce_display(self, obj):
        if obj.is_bounce:
            return format_html('<span style="color: red; font-weight: bold;">ارتداد</span>')
        return format_html('<span style="color: green;">عادي</span>')
    is_bounce_display.short_description = 'النوع'

@admin.register(RealTimeVisitor)
class RealTimeVisitorAdmin(admin.ModelAdmin):
    list_display = ['session_link', 'current_page_short', 'time_on_page_display', 
                    'is_online_display', 'last_activity']
    list_filter = ['last_activity']
    readonly_fields = ['last_activity']
    
    def session_link(self, obj):
        url = f"/admin/analytics/visitorsession/{obj.session.id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.session.session_id_short())
    session_link.short_description = 'الجلسة'
    
    def current_page_short(self, obj):
        return (obj.current_page[:50] + '...') if len(obj.current_page) > 50 else obj.current_page
    current_page_short.short_description = 'الصفحة الحالية'
    
    def time_on_page_display(self, obj):
        return str(obj.time_on_page)
    time_on_page_display.short_description = 'الوقت في الصفحة'
    
    def is_online_display(self, obj):
        if obj.is_online:
            return format_html('<span style="color: green;">● متصل</span>')
        return format_html('<span style="color: gray;">● غير متصل</span>')
    is_online_display.short_description = 'الحالة'

@admin.register(AnalyticsDashboard)
class AnalyticsDashboardAdmin(admin.ModelAdmin):
    list_display = ['name', 'refresh_interval', 'is_default']
    list_filter = ['is_default']

@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'alert_type_display', 'threshold', 'enabled_display', 'last_triggered']
    list_filter = ['alert_type', 'enabled']
    
    def alert_type_display(self, obj):
        return dict(obj.ALERT_TYPES)[obj.alert_type]
    alert_type_display.short_description = 'نوع التنبيه'
    
    def enabled_display(self, obj):
        if obj.enabled:
            return format_html('<span style="color: green;">● مفعل</span>')
        return format_html('<span style="color: red;">● معطل</span>')
    enabled_display.short_description = 'الحالة'