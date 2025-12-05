from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from datetime import timedelta, datetime
import requests
import logging

logger = logging.getLogger(__name__)


def check_contact_reminders():
    """检查需要联系的客户并发送提醒"""
    from .models import Customer
    
    # 获取当前时间(精确到分钟)
    now = timezone.now()
    current_minute = now.replace(second=0, microsecond=0)
    next_minute = current_minute + timedelta(minutes=1)
    
    # 查询下次联系时间在当前分钟的客户
    customers = Customer.objects.filter(
        next_contact_time__gte=current_minute,
        next_contact_time__lt=next_minute,
        sales_rep__isnull=False
    )
    
    # 企业微信webhook配置
    WECOM_WEBHOOK_KEY = "4ff08824-5bbe-44c7-bfdf-c25ce27a4170"
    webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={WECOM_WEBHOOK_KEY}"
    
    for customer in customers:
        # 格式: "@销售代表 下次联系时间 客户姓名 状态"
        sales_rep_name = customer.sales_rep.username if customer.sales_rep else "无"
        status_display = customer.get_status_display()
        
        # 将UTC时间转换为北京时间
        local_time = timezone.localtime(customer.next_contact_time)
        next_time = local_time.strftime('%Y-%m-%d %H:%M')
        
        message = f"@{sales_rep_name} {next_time} {customer.name} {status_display}"
        
        logger.info(f"[联系提醒] {message}")
        
        # 发送企业微信webhook
        try:
            response = requests.post(webhook_url, json={
                "msgtype": "text",
                "text": {
                    "content": message,
                    "mentioned_list": [sales_rep_name]  # @指定销售
                }
            }, timeout=5)
            
            if response.status_code == 200:
                logger.info(f"[企业微信] 提醒发送成功: {message}")
            else:
                logger.error(f"[企业微信] 提醒发送失败,状态码: {response.status_code}")
        except Exception as e:
            logger.error(f"[企业微信] 提醒发送失败: {e}")


def recycle_unreachable_leads():
    """自动回收无法联系的线索到公海"""
    from .models import Customer
    
    # 30天前的时间点
    thirty_days_ago = timezone.now() - timedelta(days=30)
    
    # 查询符合回收条件的客户
    customers = Customer.objects.filter(
        status='unreachable',
        last_contact_at__lt=thirty_days_ago,
        sales_rep__isnull=False
    )
    
    count = customers.count()
    if count > 0:
        # 回收到公海(设置sales_rep为None)
        customers.update(sales_rep=None)
        logger.info(f"[自动回收] 成功回收 {count} 个无法联系的线索到公海")
    else:
        logger.info("[自动回收] 没有需要回收的线索")


def start_scheduler():
    """启动调度器"""
    scheduler = BackgroundScheduler()
    
    # 任务1: 每分钟检查联系提醒
    scheduler.add_job(
        check_contact_reminders,
        'interval',
        minutes=1,
        id='check_contact_reminders',
        replace_existing=True
    )
    
    # 任务2: 每天凌晨2点自动回收线索
    scheduler.add_job(
        recycle_unreachable_leads,
        'cron',
        hour=2,
        minute=0,
        id='recycle_unreachable_leads',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("[调度器] 后台任务调度器已启动")
    logger.info("[调度器] - 联系提醒: 每分钟执行一次")
    logger.info("[调度器] - 线索回收: 每天02:00执行")
