from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Customer(models.Model):
    """客户/线索模型"""
    
    STATUS_CHOICES = [
        ('wait_contact', '待沟通'),
        ('wait_followup', '待跟进'),
        ('wait_visit', '待到访'),
        ('visited', '已到访'),
        ('signed', '已签约'),
        ('no_intent', '无意向'),
        ('unreachable', '未接通'),
    ]
    
    # 基础字段
    name = models.CharField('客户姓名', max_length=100)
    phone = models.CharField('电话号码', max_length=20, unique=True)
    
    # 销售关系(None=公海, 非None=私海)
    sales_rep = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='销售代表',
        related_name='customers'
    )
    
    # 状态与来源
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='wait_contact')
    source = models.CharField('线索来源', max_length=100, blank=True)
    
    # 地域信息
    city_auto = models.CharField('自动定位城市', max_length=50, blank=True)
    region_manual = models.CharField('手动填写地域', max_length=100, blank=True)
    
    # 联系相关
    contact_count = models.PositiveIntegerField('联系次数', default=0)
    next_contact_time = models.DateTimeField('下次联系时间', null=True, blank=True)
    
    # 时间戳(使用default=timezone.now允许导入历史时间)
    created_at = models.DateTimeField('创建时间', default=timezone.now)
    last_contact_at = models.DateTimeField('最后联系时间', auto_now=True)
    
    # 重点客户标记
    is_key_customer = models.BooleanField('重点客户', default=False)
    
    # 备注信息
    notes = models.TextField('备注信息', blank=True, default='')
    
    # 省份信息
    province = models.CharField('省份', max_length=50, blank=True, default='')
    
    # 扩展字段(支持自定义字段)
    extra_data = models.JSONField('扩展数据', default=dict, blank=True)
    
    class Meta:
        verbose_name = '客户'
        verbose_name_plural = '客户'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        """
        保存客户信息，自动增加沟通次数
        当 next_contact_time 被修改时，contact_count 自动加 1
        """
        # 如果是更新操作（已有 pk）
        if self.pk:
            try:
                # 从数据库获取旧值
                old_instance = Customer.objects.get(pk=self.pk)
                
                # 检查 next_contact_time 是否被修改
                old_time = old_instance.next_contact_time
                new_time = self.next_contact_time
                
                # 如果时间被修改了（不同的值，且新值不为 None）
                if old_time != new_time and new_time is not None:
                    self.contact_count += 1
            except Customer.DoesNotExist:
                # 如果旧实例不存在，不做处理
                pass
        
        # 调用父类的 save 方法
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.phone})"


class CustomField(models.Model):
    """自定义字段定义模型"""
    
    FIELD_TYPE_CHOICES = [
        ('text', '文本'),
        ('textarea', '多行文本'),
        ('number', '数字'),
        ('date', '日期'),
        ('datetime', '日期时间'),
        ('select', '单选下拉'),
        ('multiselect', '多选'),
    ]
    
    # 字段标识符（用于存储在extra_data中的key）
    field_name = models.CharField('字段标识符', max_length=50, unique=True, help_text='英文字母和下划线，如: custom_budget')
    
    # 显示标签
    label = models.CharField('显示名称', max_length=100, help_text='显示给用户的字段名称')
    
    # 字段类型
    field_type = models.CharField('字段类型', max_length=20, choices=FIELD_TYPE_CHOICES, default='text')
    
    # 选项配置（用于select和multiselect类型）
    options = models.JSONField('选项配置', default=list, blank=True, help_text='格式: ["选项1", "选项2", "选项3"]')
    
    # 验证规则
    is_required = models.BooleanField('是否必填', default=False)
    placeholder = models.CharField('占位符文本', max_length=200, blank=True)
    help_text = models.CharField('帮助文本', max_length=200, blank=True)
    
    # 排序和状态
    order = models.PositiveIntegerField('排序', default=0, help_text='数字越小越靠前')
    is_active = models.BooleanField('是否启用', default=True)
    
    # 创建时间
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '自定义字段'
        verbose_name_plural = '自定义字段'
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return f"{self.label} ({self.field_name})"

