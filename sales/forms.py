from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from captcha.fields import CaptchaField
from .models import Customer
import json


class CaptchaAuthenticationForm(AuthenticationForm):
    """带验证码的登录表单"""
    captcha = CaptchaField(label='验证码')

class CustomerForm(forms.ModelForm):
    """客户信息表单"""
    
    # 最近联系时间（只读显示）
    last_contact_at = forms.DateTimeField(
        label='最近联系时间',
        required=False,
        disabled=True,
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly'
        })
    )
    
    # 自定义字段显示
    next_contact_time = forms.DateTimeField(
        label='下次联系时间',
        required=False,
        widget=forms.DateTimeInput(attrs={
            'type': 'datetime-local',
            'class': 'form-control'
        })
    )
    
    # 销售经理选择字段
    sales_rep = forms.ModelChoiceField(
        label='销售经理',
        queryset=User.objects.filter(is_staff=True),
        required=False,
        empty_label='公海（无销售经理）',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # 备注信息
    extra_data = forms.CharField(
        label='备注信息',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '客户备注信息'
        })
    )
    
    # 省份选项
    PROVINCE_CHOICES = [
        ('', '请选择省份'),
        ('北京', '北京'), ('上海', '上海'), ('天津', '天津'), ('重庆', '重庆'),
        ('河北', '河北'), ('山西', '山西'), ('辽宁', '辽宁'), ('吉林', '吉林'),
        ('黑龙江', '黑龙江'), ('江苏', '江苏'), ('浙江', '浙江'), ('安徽', '安徽'),
        ('福建', '福建'), ('江西', '江西'), ('山东', '山东'), ('河南', '河南'),
        ('湖北', '湖北'), ('湖南', '湖南'), ('广东', '广东'), ('海南', '海南'),
        ('四川', '四川'), ('贵州', '贵州'), ('云南', '云南'), ('陕西', '陕西'),
        ('甘肃', '甘肃'), ('青海', '青海'), ('台湾', '台湾'),
        ('内蒙古', '内蒙古'), ('广西', '广西'), ('西藏', '西藏'), ('宁夏', '宁夏'),
        ('新疆', '新疆'), ('香港', '香港'), ('澳门', '澳门'),
    ]
    
    # 省份字段
    province = forms.ChoiceField(
        label='省份',
        choices=PROVINCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # 备注字段
    notes = forms.CharField(
        label='重要备注',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': '记录客户的重要信息和备注'
        })
    )
    
    # 重点客户标记
    is_key_customer = forms.BooleanField(
        label='标记为重点客户',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Customer
        fields = [
            'name', 'phone', 'status', 
            'city_auto', 'region_manual', 'province',
            'sales_rep', 'next_contact_time', 
            'notes', 'is_key_customer'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '客户姓名'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '联系电话'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'city_auto': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '自动定位城市'}),
            'region_manual': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '手动填写地域'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 导入CustomField模型
        from .models import CustomField
        
        # 加载备注信息（兼容旧数据）
        if self.instance and self.instance.pk and self.instance.extra_data:
            if isinstance(self.instance.extra_data, dict):
                self.initial['extra_data'] = self.instance.extra_data.get('note', '')
            else:
                self.initial['extra_data'] = str(self.instance.extra_data)
        
        # 如果是编辑模式，且last_contact_at存在，则初始化
        if self.instance and self.instance.pk and self.instance.last_contact_at:
            self.initial['last_contact_at'] = self.instance.last_contact_at
        
        # 动态添加自定义字段
        custom_fields = CustomField.objects.filter(is_active=True).order_by('order')
        
        for custom_field in custom_fields:
            # 直接使用field_name，不要再加custom_前缀（因为field_name已经是custom_field_1格式）
            field_name = custom_field.field_name
            
            # 根据字段类型创建表单字段
            if custom_field.field_type == 'text':
                field = forms.CharField(
                    label=custom_field.label,
                    required=custom_field.is_required,
                    widget=forms.TextInput(attrs={
                        'class': 'form-control',
                        'placeholder': custom_field.placeholder
                    })
                )
            elif custom_field.field_type == 'textarea':
                field = forms.CharField(
                    label=custom_field.label,
                    required=custom_field.is_required,
                    widget=forms.Textarea(attrs={
                        'class': 'form-control',
                        'rows': 3,
                        'placeholder': custom_field.placeholder
                    })
                )
            elif custom_field.field_type == 'number':
                field = forms.DecimalField(
                    label=custom_field.label,
                    required=custom_field.is_required,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'placeholder': custom_field.placeholder
                    })
                )
            elif custom_field.field_type == 'date':
                field = forms.DateField(
                    label=custom_field.label,
                    required=custom_field.is_required,
                    widget=forms.DateInput(attrs={
                        'type': 'date',
                        'class': 'form-control'
                    })
                )
            elif custom_field.field_type == 'datetime':
                field = forms.DateTimeField(
                    label=custom_field.label,
                    required=custom_field.is_required,
                    widget=forms.DateTimeInput(attrs={
                        'type': 'datetime-local',
                        'class': 'form-control'
                    })
                )
            elif custom_field.field_type == 'select':
                choices = [('', '请选择')] + [(opt, opt) for opt in custom_field.options]
                field = forms.ChoiceField(
                    label=custom_field.label,
                    required=custom_field.is_required,
                    choices=choices,
                    widget=forms.Select(attrs={'class': 'form-select'})
                )
            elif custom_field.field_type == 'multiselect':
                choices = [(opt, opt) for opt in custom_field.options]
                field = forms.MultipleChoiceField(
                    label=custom_field.label,
                    required=custom_field.is_required,
                    choices=choices,
                    widget=forms.SelectMultiple(attrs={'class': 'form-select'})
                )
            else:
                continue
            
            # 如果有帮助文本，添加到字段
            if custom_field.help_text:
                field.help_text = custom_field.help_text
            
            # 添加字段到表单
            self.fields[field_name] = field
            
            # 如果是编辑模式，加载已有的值
            if self.instance and self.instance.pk and self.instance.extra_data:
                if isinstance(self.instance.extra_data, dict):
                    value = self.instance.extra_data.get(custom_field.field_name)
                    if value is not None:
                        self.initial[field_name] = value
    
    def save(self, commit=True):
        """保存表单，包括处理extra_data"""
        from .models import CustomField
        
        instance = super().save(commit=False)
        
        # 获取备注信息
        note = self.cleaned_data.get('extra_data', '').strip()
        
        # 构建extra_data字典
        data = {}
        if note:
            data['note'] = note
        
        # 获取所有启用的自定义字段并保存它们的值
        custom_fields = CustomField.objects.filter(is_active=True)
        
        for custom_field in custom_fields:
            field_name = custom_field.field_name
            # 从cleaned_data获取值
            value = self.cleaned_data.get(field_name)
            
            # 只保存有值的字段
            if value is not None and value != '':
                # 对于多选字段，保持列表格式
                if custom_field.field_type == 'multiselect' and isinstance(value, list):
                    data[custom_field.field_name] = value
                # 对于日期/时间字段，转换为字符串
                elif custom_field.field_type in ['date', 'datetime']:
                    data[custom_field.field_name] = str(value)
                # 其他字段直接保存
                else:
                    data[custom_field.field_name] = str(value)
        
        # 设置extra_data
        instance.extra_data = data if data else {}
        
        if commit:
            instance.save()
        
        return instance



class ImportForm(forms.Form):
    """批量导入表单"""
    excel_file = forms.FileField(
        label='Excel文件',
        help_text='请上传包含客户数据的Excel文件',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.xlsx,.xls'})
    )


class UserManagementForm(UserCreationForm):
    """用户管理表单"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    is_staff = forms.BooleanField(
        required=False,
        label='员工权限',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'is_staff']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def save(self, commit=True):
        """重写save方法以正确保存email和is_staff字段"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_staff = self.cleaned_data.get('is_staff', False)
        
        if commit:
            user.save()
        
        return user

