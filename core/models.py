from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.conf import settings
from ckeditor.fields import RichTextField
from PIL import Image
import os
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime
from ckeditor.fields import RichTextField
from django.core.exceptions import ValidationError


class Category(models.Model):
    CATEGORY_TYPES = [
        ('courses', 'الكورسات'),
        ('articles', 'المقالات'),
        ('grants', 'المنح والتدريبات'),
        ('books', 'الكتب والملخصات'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="الاسم")
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES, verbose_name="نوع الفئة")
    description = models.TextField(blank=True, verbose_name="الوصف")
    icon = models.CharField(max_length=50, blank=True, verbose_name="الأيقونة")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    
    class Meta:
        verbose_name = 'القسم'
        verbose_name_plural = 'الأقسام'
        ordering = ['name']
    
    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return f"{reverse('search')}?category={self.category_type}"


class Post(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'مسودة'
        PUBLISHED = 'published', 'منشور'
        PRIVATE = 'private', 'خاص'
        ARCHIVED = 'archived', 'مؤرشف'

    # المعلومات الأساسية
    title = models.CharField(max_length=200, verbose_name="العنوان")
    slug = models.SlugField(max_length=250, unique=True, verbose_name="الرابط")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts', verbose_name="الفئة")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posts', verbose_name="المؤلف")

    # المحتوى
    content = RichTextField(verbose_name="المحتوى")
    
    # الصور (القديم والجديد معاً)
    image = models.ImageField(upload_to='posts/featured/%Y/%m/%d/', blank=True, verbose_name="الصورة القديمة")
    featured_image = models.ImageField(upload_to='posts/featured/%Y/%m/', blank=True, verbose_name="الصورة الرئيسية")
    thumbnail = models.ImageField(upload_to='posts/thumbnails/%Y/%m/', blank=True, verbose_name="الصورة المصغرة")

    excerpt = models.TextField(max_length=300, blank=True, verbose_name="الملخص")

    # الروابط
    link = models.URLField(blank=True, null=True, verbose_name="رابط خارجي")
    link_delay = models.IntegerField(default=30, blank=True, null=True, verbose_name="تأخير الرابط")

    # الإحصائيات
    views = models.PositiveIntegerField(default=0, verbose_name="المشاهدات")

    # حالة النشر
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT, verbose_name="الحالة")
    publish_date = models.DateTimeField(blank=True, null=True, verbose_name="تاريخ النشر")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    # SEO
    seo_title = models.CharField(max_length=200, blank=True, verbose_name="عنوان SEO")
    seo_description = models.TextField(max_length=300, blank=True, verbose_name="وصف SEO")
    seo_keywords = models.CharField(max_length=200, blank=True, verbose_name="كلمات مفتاحية SEO")

    class Meta:
        verbose_name = 'منشور'
        verbose_name_plural = 'المنشورات'
        ordering = ['-publish_date', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # إنشاء slug تلقائياً إذا لم يكن موجوداً
        if not self.slug:
            base = slugify(self.title, allow_unicode=True) or "post"
            slug = base
            i = 1
            while Post.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{i}"
                i += 1
            self.slug = slug
        
        # نشر تلقائي
        if self.status == self.Status.PUBLISHED and not self.publish_date:
            self.publish_date = timezone.now()
        
        super().save(*args, **kwargs)
        
        # إنشاء thumbnail تلقائياً إذا كانت featured_image موجودة
        if self.featured_image and not self.thumbnail:
            self.create_thumbnail()

    def create_thumbnail(self):
        """إنشاء صورة مصغرة من الصورة الرئيسية"""
        if not self.featured_image:
            return
        
        try:
            image = Image.open(self.featured_image.path)
            image.thumbnail((400, 300), Image.Resampling.LANCZOS)
            
            thumb_path = self.featured_image.path.replace("featured", "thumbnails")
            os.makedirs(os.path.dirname(thumb_path), exist_ok=True)
            image.save(thumb_path)
            
            self.thumbnail.name = thumb_path.split("media/")[-1]
            self.save(update_fields=["thumbnail"])
        except Exception as e:
            print(f"خطأ في إنشاء الصورة المصغرة: {e}")

    def get_absolute_url(self):
        return reverse("post_detail", kwargs={"slug": self.slug})

    def increment_views(self):
        Post.objects.filter(pk=self.pk).update(views=models.F("views") + 1)

    @property
    def display_title(self):
        return self.seo_title or self.title

    @property
    def display_description(self):
        return self.seo_description or self.excerpt or self.content[:160]
    
    @property
    def get_main_image(self):
        """الحصول على الصورة الرئيسية (الأفضلية للصورة الجديدة ثم القديمة)"""
        return self.featured_image or self.image


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments', verbose_name="المنشور")
    name = models.CharField(max_length=100, verbose_name="الاسم")
    email = models.EmailField(verbose_name="البريد الإلكتروني")
    content = models.TextField(verbose_name="المحتوى")
    is_approved = models.BooleanField(default=False, verbose_name="معتمد")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    
    class Meta:
        verbose_name = 'تعليق'
        verbose_name_plural = 'التعليقات'
        ordering = ['-created_at']
    
    def __str__(self):
        return f'تعليق بواسطة {self.name} على {self.post.title}'


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=200, default='موقع التعليم', verbose_name="اسم الموقع")
    site_description = models.TextField(blank=True, null=True, verbose_name="وصف الموقع")
    site_logo = models.ImageField(upload_to='site/', blank=True, null=True, verbose_name="شعار الموقع")
    
    # إعدادات المحتوى
    default_link_delay = models.IntegerField(default=30, help_text='التأخير الافتراضي بالثواني', verbose_name="تأخير الرابط الافتراضي")
    allow_comments = models.BooleanField(default=True, verbose_name="السماح بالتعليقات")
    require_comment_approval = models.BooleanField(default=True, verbose_name="يتطلب موافقة على التعليقات")
    
    # إعدادات النظام
    maintenance_mode = models.BooleanField(default=False, verbose_name="وضع الصيانة")
    contact_email = models.EmailField(default='contact@example.com', verbose_name="البريد الإلكتروني للتواصل")
    
    # وسائل التواصل الاجتماعي
    facebook_url = models.URLField(blank=True, null=True, verbose_name="رابط الفيسبوك")
    instagram_url = models.URLField(blank=True, null=True, verbose_name="رابط إنستغرام")
    youtube_url = models.URLField(blank=True, null=True, verbose_name="رابط يوتيوب")
    
    # التواريخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    def __str__(self):
        return self.site_name
    
    class Meta:
        verbose_name = 'إعدادات الموقع'
        verbose_name_plural = 'إعدادات الموقع'

class heroSection(models.Model):
    title = models.CharField(max_length=200, verbose_name="العنوان")
    subtitle = models.CharField(max_length=300, blank=True, verbose_name="العنوان الفرعي")
    background_image = models.ImageField(upload_to='site/hero/', blank=True, null=True, verbose_name="صورة الخلفية")
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'hero قسم'
        verbose_name_plural = 'hero قسم'


class SystemLog(models.Model):
    """سجلات النظام"""
    LOG_TYPES = (
        ('info', 'معلومات'),
        ('warning', 'تحذير'),
        ('error', 'خطأ'),
        ('security', 'أمني'),
    )
    
    log_type = models.CharField(max_length=20, choices=LOG_TYPES, default='info', verbose_name="نوع السجل")
    message = models.TextField(verbose_name="الرسالة")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="المستخدم")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="عنوان IP")
    user_agent = models.TextField(blank=True, null=True, verbose_name="معلومات المتصفح")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    
    def __str__(self):
        return f"{self.get_log_type_display()} - {self.message[:50]}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'سجل النظام'
        verbose_name_plural = 'سجلات النظام'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name="المستخدم")
    full_name = models.CharField(max_length=255, blank=True, verbose_name="الاسم الكامل")
    bio = models.TextField(blank=True, null=True, verbose_name="السيرة الذاتية")
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True, verbose_name="صورة الملف الشخصي")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="الهاتف")
    birth_date = models.DateField(blank=True, null=True, verbose_name="تاريخ الميلاد")
    
    # الصلاحيات
    is_content_editor = models.BooleanField(default=False, verbose_name='محرر محتوى')
    can_manage_comments = models.BooleanField(default=False, verbose_name='يمكنه إدارة التعليقات')
    can_manage_categories = models.BooleanField(default=False, verbose_name='يمكنه إدارة الأقسام')

    # الإحصائيات
    posts_count = models.IntegerField(default=0, verbose_name="عدد المنشورات")
    comments_count = models.IntegerField(default=0, verbose_name="عدد التعليقات")
    last_active = models.DateTimeField(auto_now=True, verbose_name="آخر نشاط")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")
    
    def __str__(self):
        return f'{self.user.username} Profile'
    
    class Meta:
        verbose_name = 'ملف المستخدم'
        verbose_name_plural = 'ملفات المستخدمين'

    def update_stats(self):
        """تحديث إحصائيات المستخدم"""
        self.posts_count = self.user.posts.count()
        self.comments_count = Comment.objects.filter(post__author=self.user).count()
        self.save(update_fields=['posts_count', 'comments_count'])




@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()