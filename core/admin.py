from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django import forms
from django.contrib import messages
from django.utils import timezone
from .models import *


class PostAdminForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'excerpt': forms.Textarea(attrs={'rows': 3}),
            'seo_description': forms.Textarea(attrs={'rows': 3}),
        }


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    list_display = (
        'get_thumbnail',
        'title',
        'category',
        'author',
        'status',
        'publish_date',
        'views',
    )
    list_filter = ('status', 'category', 'publish_date', 'created_at')
    search_fields = ('title', 'content', 'excerpt')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publish_date'
    readonly_fields = (
        'views',
        'created_at',
        'updated_at',
        'get_featured_image_preview',
        'get_thumbnail_preview',
    )
    
    fieldsets = (
        (_('المعلومات الأساسية'), {
            'fields': (
                'title',
                'slug',
                'category',
                'author',
                'status',
                'publish_date',
            )
        }),
        (_('المحتوى'), {
            'fields': (
                'excerpt',
                'content',
                'link',
                'link_delay',
            )
        }),
        (_('الصور'), {
            'fields': (
                'featured_image',
                'get_featured_image_preview',
                'thumbnail',
                'get_thumbnail_preview',
            )
        }),
        (_('إحصائيات'), {
            'fields': (
                'views',
                'created_at',
                'updated_at',
            )
        }),
        (_('تحسين محركات البحث'), {
            'fields': (
                'seo_title',
                'seo_description',
                'seo_keywords',
            ),
            'classes': ('collapse',)
        }),
    )
    
    
    def get_thumbnail(self, obj):
        if obj.thumbnail:
            return format_html(
                f'<img src="{obj.thumbnail.url}" style="width: 50px; height: 50px; object-fit: cover;" />'
            )
        elif obj.featured_image:
            return format_html(
                f'<img src="{obj.featured_image.url}" style="width: 50px; height: 50px; object-fit: cover;" />'
            )
        return '-'
    get_thumbnail.short_description = _('صورة مصغرة')
    
    def get_featured_image_preview(self, obj):
        if obj.featured_image:
            return format_html(
                f'<img src="{obj.featured_image.url}" style="max-width: 300px; max-height: 200px;" />'
            )
        return _('لا توجد صورة رئيسية')
    get_featured_image_preview.short_description = _('معاينة الصورة الرئيسية')
    
    def get_thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html(
                f'<img src="{obj.thumbnail.url}" style="max-width: 200px; max-height: 150px;" />'
            )
        return _('لا توجد صورة مصغرة')
    get_thumbnail_preview.short_description = _('معاينة الصورة المصغرة')
    
    actions = ['make_published', 'make_draft', 'duplicate_post']
    
    def make_published(self, request, queryset):
        updated = queryset.update(
            status=Post.Status.PUBLISHED,
            publish_date=timezone.now()
        )
        self.message_user(request, f'تم نشر {updated} منشور')
    make_published.short_description = _('نشر المنشورات المحددة')
    
    def make_draft(self, request, queryset):
        updated = queryset.update(status=Post.Status.DRAFT)
        self.message_user(request, f'تم تحويل {updated} منشور إلى مسودة')
    make_draft.short_description = _('تحويل إلى مسودة')
    
    def duplicate_post(self, request, queryset):
        for post in queryset:
            new_post = Post.objects.get(pk=post.pk)
            new_post.pk = None
            new_post.slug = f"{post.slug}-copy-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            new_post.title = f"{post.title} (نسخة)"
            new_post.status = Post.Status.DRAFT
            new_post.views = 0
            new_post.save()
        
        self.message_user(request, f'تم نسخ {queryset.count()} منشور')
    duplicate_post.short_description = _('نسخ المنشورات المحددة')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category_type', 'get_icon', 'post_count', 'created_at')
    list_filter = ('category_type', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {}  # لا يوجد حقل slug في النموذج

    def get_icon(self, obj):
        if obj.icon:
            return format_html('<i class="{}"></i> {}'.format(obj.icon, obj.icon))
        return '-'
    get_icon.short_description = _('الأيقونة')

    def post_count(self, obj):
        # تصحيح reverse ليناسب app core و model Post
        try:
            url = reverse('admin:core_post_changelist') + f'?category__id__exact={obj.id}'
        except Exception:
            url = '#'
        count = obj.posts.count()
        return format_html('<a href="{}">{}</a>', url, count)
    post_count.short_description = _('عدد المنشورات')


class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'post', 'is_approved', 'created_at', 'short_content')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('name', 'email', 'content', 'post__title')
    actions = ['approve_comments', 'disapprove_comments']
    
    def short_content(self, obj):
        content = obj.content[:50]
        if len(obj.content) > 50:
            content += '...'
        return content
    short_content.short_description = _('المحتوى')
    
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'تم تفعيل {updated} تعليق')
    approve_comments.short_description = _('تفعيل التعليقات المحددة')
    
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, f'تم تعطيل {updated} تعليق')
    disapprove_comments.short_description = _('تعطيل التعليقات المحددة')


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # منع إضافة أكثر من سجل واحد
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'is_content_editor',
        'can_manage_comments',
        'can_manage_categories',
        'posts_count',
        'last_active',
    )

    list_filter = (
        'is_content_editor',
        'can_manage_comments',
        'can_manage_categories',
    )

    search_fields = ('user__username', 'full_name')


# التسجيل التقليدي للنماذج (عدا SiteSettings الذي سجلناه أعلاه)
admin.site.register(Comment, CommentAdmin)

# تحسين واجهة الإدارة
admin.site.site_header = 'إدارة المدونة'
admin.site.site_title = 'نظام إدارة المدونة'
admin.site.index_title = 'مرحبا بك في لوحة التحكم'