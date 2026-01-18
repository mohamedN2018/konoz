from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import (
    AuthenticationForm, 
    UserCreationForm, 
    PasswordResetForm, 
    SetPasswordForm,
    PasswordChangeForm
)
from .models import *

# ======== وظيفة مساعدة للتنسيق التلقائي ========
def apply_field_styling(field, field_type, label=None):
    """تطبيق تنسيق تلقائي على حقل مع دعم Dark Mode"""
    if not field.widget.attrs:
        field.widget.attrs = {}
    
    # إضافة class عام مع دعم Dark Mode
    base_classes = 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition duration-200'
    dark_classes = ' dark:bg-gray-800 dark:text-white dark:border-gray-600 dark:focus:ring-blue-400 dark:focus:border-blue-400'
    
    if 'class' not in field.widget.attrs:
        field.widget.attrs['class'] = base_classes + dark_classes
    else:
        if 'w-full' not in field.widget.attrs['class']:
            field.widget.attrs['class'] = base_classes + ' ' + field.widget.attrs['class'] + dark_classes
    
    # حسب نوع الحقل
    if field_type in ['CharField', 'EmailField', 'URLField', 'SlugField']:
        if hasattr(field, 'max_length') and field.max_length:
            field.widget.attrs['maxlength'] = str(field.max_length)
    
    elif field_type == 'TextField':
        if not field.widget.attrs.get('rows'):
            field.widget.attrs['rows'] = 4
        field.widget.attrs['class'] += ' resize-y'
    
    elif field_type == 'IntegerField':
        field.widget.attrs['type'] = 'number'
    
    elif field_type == 'DateField':
        field.widget.attrs['type'] = 'date'
    
    elif field_type == 'DateTimeField':
        field.widget.attrs['type'] = 'datetime-local'
    
    elif field_type == 'BooleanField':
        field.widget.attrs['class'] = 'form-check-input dark:bg-gray-700'
    
    elif field_type == 'ChoiceField':
        field.widget.attrs['class'] += ' cursor-pointer'
    
    return field


def auto_style_form(form_class):
    """ديكوراتور لتطبيق التنسيق التلقائي"""
    class AutoStyledForm(form_class):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for field_name, field in self.fields.items():
                if field_name not in ['password', 'password1', 'password2', 'old_password']:
                    field_type = type(field).__name__
                    label = field.label or field_name.replace('_', ' ').title()
                    field = apply_field_styling(field, field_type, label)
    
    return AutoStyledForm


# ======== فئة أساسية لجميع الفورمس ========
class StyledForm(forms.Form):
    """فئة أساسية مع تنسيق تلقائي"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_all_fields()
    
    def style_all_fields(self):
        """تطبيق التنسيق على جميع الحقول"""
        for field_name, field in self.fields.items():
            if field_name not in ['password', 'password1', 'password2', 'old_password']:
                field_type = type(field).__name__
                label = field.label or field_name.replace('_', ' ').title()
                field = apply_field_styling(field, field_type, label)


class StyledModelForm(forms.ModelForm):
    """فئة أساسية ModelForm مع تنسيق تلقائي"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_all_fields()
    
    def style_all_fields(self):
        """تطبيق التنسيق على جميع الحقول"""
        for field_name, field in self.fields.items():
            if field_name not in ['password', 'password1', 'password2', 'old_password']:
                field_type = type(field).__name__
                label = field.label or field_name.replace('_', ' ').title()
                field = apply_field_styling(field, field_type, label)


# ======== فورمس المصادقة ========
@auto_style_form
class LoginForm(AuthenticationForm):
    username = forms.CharField(label='اسم المستخدم أو البريد الإلكتروني')
    password = forms.CharField(label='كلمة المرور', widget=forms.PasswordInput())
    remember_me = forms.BooleanField(
        required=False,
        label='تذكرني',
        widget=forms.CheckboxInput()
    )


@auto_style_form
class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='البريد الإلكتروني', max_length=254)
    first_name = forms.CharField(max_length=30, required=False, label='الاسم الأول')
    last_name = forms.CharField(max_length=30, required=False, label='اسم العائلة')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'placeholder': 'اختر اسم مستخدم فريد'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'أدخل كلمة المرور'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'أعد إدخال كلمة المرور'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('هذا البريد الإلكتروني مستخدم بالفعل!')
        return email


# ======== فورمس كلمة المرور ========
@auto_style_form
class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label='البريد الإلكتروني', max_length=254)


@auto_style_form
class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label='كلمة المرور الجديدة', widget=forms.PasswordInput())
    new_password2 = forms.CharField(label='تأكيد كلمة المرور', widget=forms.PasswordInput())


@auto_style_form
class ChangePasswordForm(PasswordChangeForm):
    old_password = forms.CharField(label='كلمة المرور الحالية', widget=forms.PasswordInput())
    new_password1 = forms.CharField(label='كلمة المرور الجديدة', widget=forms.PasswordInput())
    new_password2 = forms.CharField(label='تأكيد كلمة المرور', widget=forms.PasswordInput())


# ======== فورمس المستخدمين ========
@auto_style_form
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['full_name', 'bio', 'profile_image', 'phone', 'birth_date']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['profile_image'].widget.attrs.update({'class': 'form-control-file'})
        self.fields['birth_date'].widget.attrs.update({'type': 'date'})


@auto_style_form
class UserRoleForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['is_content_editor', 'can_manage_comments', 'can_manage_categories']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-check-input'})


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']


# ======== فورم المنشورات ========
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title', 'category', 'content', 
            'image', 'featured_image',
            'excerpt', 'link', 'link_delay', 'status',
            'seo_title', 'seo_description', 'seo_keywords',
            'publish_date'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'أدخل عنوان المنشور',
                'required': True,
                'class': 'form-control dark:bg-gray-800 dark:text-white dark:border-gray-600'
            }),
            'category': forms.Select(attrs={
                'required': True,
                'class': 'form-control dark:bg-gray-800 dark:text-white dark:border-gray-600'
            }),
            'content': forms.Textarea(attrs={
                'rows': 10,
                'id': 'post_content_field',
                'class': 'form-control dark:bg-gray-800 dark:text-white dark:border-gray-600'
            }),
            'image': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control dark:bg-gray-800 dark:text-white dark:border-gray-600'
            }),
            'featured_image': forms.FileInput(attrs={
                'accept': 'image/*',
                'class': 'form-control dark:bg-gray-800 dark:text-white dark:border-gray-600'
            }),
            'excerpt': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'ملخص مختصر للمنشور',
                'maxlength': '300',
                'class': 'form-control dark:bg-gray-800 dark:text-white dark:border-gray-600'
            }),
            'link': forms.URLInput(attrs={
                'placeholder': 'https://example.com',
                'class': 'form-control dark:bg-gray-800 dark:text-white dark:border-gray-600'
            }),
            'link_delay': forms.NumberInput(attrs={
                'min': 0,
                'max': 300,
                'class': 'form-control dark:bg-gray-800 dark:text-white dark:border-gray-600'
            }),
            'status': forms.Select(attrs={
                'class': 'form-control dark:bg-gray-800 dark:text-white dark:border-gray-600'
            }),
            'seo_title': forms.TextInput(attrs={
                'placeholder': 'عنوان لمحركات البحث',
                'class': 'form-control dark:bg-gray-800 dark:text-white dark:border-gray-600'
            }),
            'seo_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'وصف لمحركات البحث',
                'maxlength': '300',
                'class': 'form-control dark:bg-gray-800 dark:text-white dark:border-gray-600'
            }),
            'seo_keywords': forms.TextInput(attrs={
                'placeholder': 'كلمات مفتاحية مفصولة بفواصل',
                'class': 'form-control dark:bg-gray-800 dark:text-white dark:border-gray-600'
            }),
            'publish_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control dark:bg-gray-800 dark:text-white dark:border-gray-600'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تطبيق التنسيق التلقائي مع دعم Dark Mode
        for field_name, field in self.fields.items():
            field_type = type(field).__name__
            label = field.label or field_name.replace('_', ' ').title()
            field = apply_field_styling(field, field_type, label)
            
            # إضافة classes خاصة للوضع الداكن إذا لم تكن موجودة
            if 'class' in field.widget.attrs:
                if 'dark:' not in field.widget.attrs['class']:
                    field.widget.attrs['class'] += ' dark:bg-gray-800 dark:text-white dark:border-gray-600'
        
        # إعدادات خاصة
        if not self['category'].value():
            self.fields['category'].empty_label = "-- اختر الفئة --"
        
        self.fields['title'].required = True
        self.fields['category'].required = True
        
        # إضافة أخطاء مخصصة للملخص
        self.fields['excerpt'].error_messages = {
            'max_length': 'الملخص لا يمكن أن يتجاوز 300 حرف.'
        }
    class Meta:
        model = Post
        fields = [
            'title', 'category', 'content', 
            'image', 'featured_image',
            'excerpt', 'link', 'link_delay', 'status',
            'seo_title', 'seo_description', 'seo_keywords',
            'publish_date'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'أدخل عنوان المنشور',
                'required': True
            }),
            'category': forms.Select(attrs={'required': True}),
            'content': forms.Textarea(attrs={
                'rows': 10,
                'id': 'post_content_field'
            }),
            'image': forms.FileInput(attrs={
                'accept': 'image/*'
            }),
            'featured_image': forms.FileInput(attrs={
                'accept': 'image/*'
            }),
            'excerpt': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'ملخص مختصر للمنشور',
                'maxlength': '300'
            }),
            'link': forms.URLInput(attrs={
                'placeholder': 'https://example.com'
            }),
            'link_delay': forms.NumberInput(attrs={
                'min': 0,
                'max': 300
            }),
            'status': forms.Select(),
            'seo_title': forms.TextInput(attrs={
                'placeholder': 'عنوان لمحركات البحث'
            }),
            'seo_description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'وصف لمحركات البحث',
                'maxlength': '300'
            }),
            'seo_keywords': forms.TextInput(attrs={
                'placeholder': 'كلمات مفتاحية مفصولة بفواصل'
            }),
            'publish_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # تطبيق التنسيق التلقائي
        for field_name, field in self.fields.items():
            field_type = type(field).__name__
            label = field.label or field_name.replace('_', ' ').title()
            field = apply_field_styling(field, field_type, label)
        
        # إعدادات خاصة
        if not self['category'].value():
            self.fields['category'].empty_label = "-- اختر الفئة --"
        
        self.fields['title'].required = True
        self.fields['category'].required = True
        
        # إضافة أخطاء مخصصة للملخص
        self.fields['excerpt'].error_messages = {
            'max_length': 'الملخص لا يمكن أن يتجاوز 300 حرف.'
        }
      
# ======== فورم التعليقات ========
@auto_style_form
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['name', 'email', 'content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }


# ======== فورم إعدادات الموقع ========
class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = '__all__'
        widgets = {
            'site_description': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field_type = type(field).__name__
            label = field.label or field_name.replace('_', ' ').title()
            field = apply_field_styling(field, field_type, label)