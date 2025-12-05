from django.contrib import admin
from django.contrib.auth.models import User
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from datetime import datetime
from .models import Customer, CustomField


class CustomerResource(resources.ModelResource):
    """客户资源类 - 处理Excel导入导出"""
    
    # 中文表头映射
    name = fields.Field(attribute='name', column_name='姓名')
    phone = fields.Field(attribute='phone', column_name='电话')
    created_at = fields.Field(attribute='created_at', column_name='线索创建时间')
    source = fields.Field(attribute='source', column_name='线索渠道')
    city_auto = fields.Field(attribute='city_auto', column_name='自动定位城市')
    region_manual = fields.Field(attribute='region_manual', column_name='手动填写地域')
    
    class Meta:
        model = Customer
        fields = ('name', 'phone', 'created_at', 'source', 'city_auto', 'region_manual')
        import_id_fields = ('phone',)  # 使用电话号码作为唯一标识
    
    def before_import_row(self, row, **kwargs):
        """导入前处理每一行数据"""
        # 处理时间格式
        if '线索创建时间' in row and row['线索创建时间']:
            try:
                # 尝试解析时间字符串
                if isinstance(row['线索创建时间'], str):
                    row['线索创建时间'] = datetime.strptime(
                        row['线索创建时间'], '%Y-%m-%d %H:%M:%S'
                    )
            except (ValueError, TypeError):
                row['线索创建时间'] = None
    
    def after_import_instance(self, instance, new, row_dict=None, **kwargs):
        """导入后处理实例"""
        # 从kwargs中获取request对象
        request = kwargs.get('request', None)
        if request and hasattr(request, 'user'):
            # 超级用户导入 -> 公海(sales_rep=None)
            # 普通员工导入 -> 私海(sales_rep=当前用户)
            if not request.user.is_superuser:
                instance.sales_rep = request.user
            else:
                instance.sales_rep = None
    
    def get_import_options(self):
        """获取导入选项"""
        options = super().get_import_options()
        return options


class MyCustomerAdmin(ImportExportModelAdmin):
    """我的客户管理"""
    resource_class = CustomerResource
    
    list_display = ['name', 'phone', 'status', 'source', 'city_auto', 
                   'contact_count', 'next_contact_time', 'created_at']
    list_filter = ['status', 'source', 'city_auto']
    search_fields = ['name', 'phone']
    readonly_fields = ['created_at', 'last_contact_at', 'contact_count']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'phone', 'status', 'source')
        }),
        ('地域信息', {
            'fields': ('city_auto', 'region_manual')
        }),
        ('联系信息', {
            'fields': ('contact_count', 'next_contact_time', 'sales_rep')
        }),
        ('时间信息', {
            'fields': ('created_at', 'last_contact_at')
        }),
        ('扩展数据', {
            'fields': ('extra_data',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """只显示当前用户的客户"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(sales_rep=request.user)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """限制销售代表选择为当前用户"""
        if db_field.name == "sales_rep":
            if not request.user.is_superuser:
                kwargs["queryset"] = User.objects.filter(id=request.user.id)
                kwargs["initial"] = request.user
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class HighSeasCustomer(Customer):
    """公海客户代理模型"""
    class Meta:
        proxy = True
        verbose_name = '公海客户'
        verbose_name_plural = '公海客户'


class HighSeasAdmin(admin.ModelAdmin):
    """公海客户管理"""
    
    list_display = ['name', 'phone', 'status', 'source', 'city_auto', 
                   'contact_count', 'created_at']
    list_filter = ['status', 'source', 'city_auto']
    search_fields = ['name', 'phone']
    
    actions = ['claim_customers']
    
    def get_queryset(self, request):
        """只显示公海客户(sales_rep为None)"""
        qs = super().get_queryset(request)
        return qs.filter(sales_rep__isnull=True)
    
    def has_add_permission(self, request):
        """禁止在公海添加客户"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """禁止在公海删除客户"""
        return False
    
    @admin.action(description='认领选中的客户')
    def claim_customers(self, request, queryset):
        """认领客户到私海"""
        updated = queryset.update(sales_rep=request.user)
        self.message_user(request, f'成功认领 {updated} 个客户')


# 自定义字段管理
class CustomFieldAdmin(admin.ModelAdmin):
    """自定义字段管理"""
    list_display = ['label', 'field_name', 'field_type', 'is_required', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    list_filter = ['field_type', 'is_active']
    search_fields = ['label', 'field_name']
    ordering = ['order', 'created_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('field_name', 'label', 'field_type')
        }),
        ('字段配置', {
            'fields': ('is_required', 'placeholder', 'help_text', 'options')
        }),
        ('显示设置', {
            'fields': ('order', 'is_active')
        }),
    )


# 注册到admin
admin.site.register(Customer, MyCustomerAdmin)
admin.site.register(HighSeasCustomer, HighSeasAdmin)
admin.site.register(CustomField, CustomFieldAdmin)

# 自定义admin站点标题
admin.site.site_header = '怪兽ABC - CRM管理系统'
admin.site.site_title = 'CRM管理'
admin.site.index_title = '欢迎使用CRM管理系统'

