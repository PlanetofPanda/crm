from django.core.management.base import BaseCommand
from sales.models import CustomField, Customer


class Command(BaseCommand):
    help = '初始化默认的自定义字段，并迁移旧的custom_field_1-4数据'

    def handle(self, *args, **options):
        self.stdout.write('开始初始化自定义字段...')
        
        # 创建默认的4个自定义字段（对应原来的custom_field_1-4）
        default_fields = [
            {
                'field_name': 'custom_field_1',
                'label': '关键信息',
                'field_type': 'text',
                'placeholder': '例如：意向加盟区域、预算范围等',
                'order': 1
            },
            {
                'field_name': 'custom_field_2',
                'label': '跟进记录',
                'field_type': 'textarea',
                'placeholder': '最新的跟进情况',
                'order': 2
            },
            {
                'field_name': 'custom_field_3',
                'label': '客户标签',
                'field_type': 'text',
                'placeholder': '例如：高意向、已到访、待签约等',
                'order': 3
            },
            {
                'field_name': 'custom_field_4',
                'label': '其他信息',
                'field_type': 'text',
                'placeholder': '其他需要记录的信息',
                'order': 4
            },
        ]
        
        created_count = 0
        for field_data in default_fields:
            field, created = CustomField.objects.get_or_create(
                field_name=field_data['field_name'],
                defaults=field_data
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ 创建自定义字段: {field.label}'))
            else:
                self.stdout.write(f'  - 自定义字段已存在: {field.label}')
        
        self.stdout.write(self.style.SUCCESS(f'\n完成！共创建 {created_count} 个自定义字段'))
        
        # 检查是否有需要迁移的旧数据
        customers_with_old_data = Customer.objects.filter(
            extra_data__has_any_keys=['custom_field_1', 'custom_field_2', 'custom_field_3', 'custom_field_4']
        )
        
        if customers_with_old_data.exists():
            count = customers_with_old_data.count()
            self.stdout.write(f'\n发现 {count} 个客户有旧格式的自定义字段数据')
            self.stdout.write(self.style.WARNING('注意：这些数据已经可以正常显示，无需额外迁移'))
        else:
            self.stdout.write('\n没有发现需要迁移的旧数据')
