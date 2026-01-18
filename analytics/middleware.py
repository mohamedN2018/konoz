# analytics/middleware.py
import geoip2.database
import geoip2.errors
from django.utils import timezone
import user_agents
from datetime import timedelta
import os
from django.conf import settings
import json
from .models import VisitorSession, PageView, Country, RealTimeVisitor

class AdvancedAnalyticsMiddleware:
    """Middleware متقدم لتتبع الزوار بدقة"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.geoip_reader = None
        
        # تحميل قاعدة بيانات GeoIP2 إذا كانت موجودة
        geoip_path = getattr(settings, 'GEOIP_PATH', None)
        if geoip_path and os.path.exists(geoip_path):
            try:
                self.geoip_reader = geoip2.database.Reader(geoip_path)
            except:
                self.geoip_reader = None
    
    def __call__(self, request):
        # تجنب تتبع طلبات AJAX أو static أو admin
        if self.should_skip_tracking(request):
            return self.get_response(request)
        
        # استخراج معلومات المستخدم
        session_key = request.session.session_key
        ip_address = self.get_client_ip(request)
        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        
        # تحليل User Agent
        user_agent = user_agents.parse(user_agent_string)
        
        # معلومات الجهاز والمتصفح
        device_info = self.get_device_info(user_agent)
        
        # معلومات جغرافية
        geo_info = self.get_geo_info(ip_address)
        
        # إنشاء أو تحديث جلسة الزائر
        visitor_session = self.create_or_update_session(
            request, session_key, ip_address, user_agent_string, device_info, geo_info
        )
        
        # تتبع المشاهدة الحالية
        if request.method == 'GET':
            self.track_page_view(request, visitor_session)
        
        # تحديث الزوار المتصلين حالياً
        self.update_realtime_visitor(visitor_session, request)
        
        # إضافة الجلسة إلى request للوصول إليها في views
        request.visitor_session = visitor_session
        
        response = self.get_response(request)
        
        # تحديث وقت النشاط بعد إرجاع الاستجابة
        self.update_session_activity(visitor_session)
        
        return response
    
    def should_skip_tracking(self, request):
        """التحقق إذا كان يجب تخطي التتبع"""
        skip_paths = [
            '/admin/', '/static/', '/media/', 
            '/api/analytics/', '/favicon.ico',
            '/health/', '/robots.txt'
        ]
        
        return any(request.path.startswith(path) for path in skip_paths)
    
    def get_client_ip(self, request):
        """استخراج عنوان IP الحقيقي"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_device_info(self, user_agent):
        """استخراج معلومات الجهاز من User Agent"""
        return {
            'device_type': 'mobile' if user_agent.is_mobile else 
                          'tablet' if user_agent.is_tablet else 
                          'desktop',
            'browser': user_agent.browser.family,
            'browser_version': user_agent.browser.version_string,
            'os': user_agent.os.family,
            'os_version': user_agent.os.version_string,
            'is_bot': user_agent.is_bot,
        }
    
    def get_geo_info(self, ip_address):
        """الحصول على المعلومات الجغرافية"""
        if not self.geoip_reader:
            return None
        
        try:
            response = self.geoip_reader.city(ip_address)
            
            # الحصول على كود الدولة وإيموجي العلم
            country_code = response.country.iso_code
            flag_emoji = self.get_flag_emoji(country_code)
            
            return {
                'country_code': country_code,
                'country_name': response.country.name,
                'country_name_ar': self.translate_country_name(response.country.name),
                'flag_emoji': flag_emoji,
                'region': response.subdivisions.most_specific.name if response.subdivisions else None,
                'city': response.city.name if response.city else None,
                'latitude': response.location.latitude,
                'longitude': response.location.longitude,
                'timezone': response.location.time_zone,
            }
        except:
            return None
    
    def get_flag_emoji(self, country_code):
        """تحويل كود الدولة إلى إيموجي علم"""
        if not country_code or len(country_code) != 2:
            return "🌐"
        
        # تحويل ASCII إلى إيموجي علم
        try:
            base = ord('🇦') - ord('A')
            emoji = ''.join(chr(ord(c.upper()) + base) for c in country_code)
            return emoji
        except:
            return "🌐"
    
    def translate_country_name(self, country_name):
        """ترجمة أسماء الدول إلى العربية"""
        translations = {
            'Egypt': 'مصر',
            'Saudi Arabia': 'السعودية',
            'United Arab Emirates': 'الإمارات',
            'Qatar': 'قطر',
            'Kuwait': 'الكويت',
            'Oman': 'عُمان',
            'Bahrain': 'البحرين',
            'Jordan': 'الأردن',
            'Lebanon': 'لبنان',
            'Syria': 'سوريا',
            'Iraq': 'العراق',
            'Yemen': 'اليمن',
            'Sudan': 'السودان',
            'Algeria': 'الجزائر',
            'Morocco': 'المغرب',
            'Tunisia': 'تونس',
            'Libya': 'ليبيا',
            'Palestine': 'فلسطين',
            'United States': 'الولايات المتحدة',
            'United Kingdom': 'المملكة المتحدة',
            'France': 'فرنسا',
            'Germany': 'ألمانيا',
            'Turkey': 'تركيا',
            'India': 'الهند',
            'China': 'الصين',
            'Russia': 'روسيا',
            'Brazil': 'البرازيل',
        }
        
        return translations.get(country_name, country_name)
    
    def create_or_update_session(self, request, session_key, ip_address, user_agent_string, device_info, geo_info):
        """إنشاء أو تحديث جلسة الزائر"""
        try:
            # البحث عن جلسة نشطة
            session = VisitorSession.objects.filter(
                session_id=session_key,
                is_active=True
            ).first()
            
            if not session:
                # إنشاء دولة جديدة إذا لم تكن موجودة
                country = None
                if geo_info:
                    country, _ = Country.objects.get_or_create(
                        code=geo_info['country_code'],
                        defaults={
                            'name': geo_info['country_name_ar'],
                            'flag_emoji': geo_info['flag_emoji']
                        }
                    )
                
                # إنشاء جلسة جديدة
                session = VisitorSession.objects.create(
                    session_id=session_key,
                    user=request.user if request.user.is_authenticated else None,
                    ip_address=ip_address,
                    user_agent=user_agent_string,
                    device_type=device_info['device_type'],
                    browser=device_info['browser'],
                    browser_version=device_info['browser_version'],
                    os=device_info['os'],
                    os_version=device_info['os_version'],
                    country=country,
                    region=geo_info['region'] if geo_info else None,
                    city=geo_info['city'] if geo_info else None,
                    latitude=geo_info['latitude'] if geo_info else None,
                    longitude=geo_info['longitude'] if geo_info else None,
                    referrer=request.META.get('HTTP_REFERER'),
                    landing_page=request.build_absolute_uri(),
                    metadata={
                        'is_bot': device_info['is_bot'],
                        'timezone': geo_info.get('timezone') if geo_info else None,
                    }
                )
            
            return session
            
        except Exception as e:
            # في حالة الخطأ، إرجاع جلسة افتراضية
            return None
    
    def track_page_view(self, request, visitor_session):
        """تتبع مشاهدة الصفحة الحالية"""
        if not visitor_session:
            return
        
        # حساب الوقت المنقضي في الصفحة السابقة
        self.update_previous_page_time(visitor_session)
        
        # تسجيل مشاهدة الصفحة الجديدة
        PageView.objects.create(
            session=visitor_session,
            url=request.build_absolute_uri(),
            title=self.get_page_title(request) or request.path,
            time_spent=timedelta(0),  # سيتم تحديثه لاحقاً
            scroll_depth=0,
            is_bounce=False
        )
        
        # زيادة عدد صفحات الجلسة
        visitor_session.page_count += 1
        visitor_session.save()
    
    def update_previous_page_time(self, visitor_session):
        """تحديث الوقت المنقضي في الصفحة السابقة"""
        if not visitor_session:
            return
        
        # البحث عن آخر مشاهدة صفحة لم يتم تحديث وقتها
        last_pageview = PageView.objects.filter(
            session=visitor_session
        ).order_by('-timestamp').first()
        
        if last_pageview and last_pageview.time_spent.total_seconds() == 0:
            # حساب الوقت المنقضي
            time_spent = timezone.now() - last_pageview.timestamp
            
            # تحديث وقت الصفحة
            last_pageview.time_spent = time_spent
            
            # تحديد إذا كانت الصفحة ارتداد (مشاهدة صفحة واحدة فقط)
            if visitor_session.page_count == 1:
                last_pageview.is_bounce = True
            
            last_pageview.save()
    
    def update_realtime_visitor(self, visitor_session, request):
        """تحديث بيانات الزائر الفوري"""
        if not visitor_session:
            return
        
        realtime_visitor, created = RealTimeVisitor.objects.get_or_create(
            session=visitor_session,
            defaults={
                'current_page': request.build_absolute_uri(),
                'time_on_page': timedelta(0),
            }
        )
        
        if not created:
            realtime_visitor.current_page = request.build_absolute_uri()
            realtime_visitor.save()
    
    def update_session_activity(self, visitor_session):
        """تحديث آخر نشاط للجلسة"""
        if visitor_session:
            visitor_session.save()
    
    def get_page_title(self, request):
        """استخراج عنوان الصفحة"""
        # يمكن تحسين هذا لاستخراج العنوان الفعلي من response
        return None
    
    def process_exception(self, request, exception):
        """معالجة الاستثناءات"""
        pass
    
    def __del__(self):
        """إغلاق قارئ GeoIP عند الإغلاق"""
        if self.geoip_reader:
            self.geoip_reader.close()