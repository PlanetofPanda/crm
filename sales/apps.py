from django.apps import AppConfig
import os


class SalesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sales"
    verbose_name = "销售管理"
    
    def ready(self):
        """应用就绪时启动后台任务"""
        # 使用文件锁确保调度器只启动一次
        import fcntl
        
        lock_file = '/tmp/monsterabc_crm_scheduler.lock'
        
        try:
            # 尝试获取独占锁
            lock_fd = open(lock_file, 'w')
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            
            # 成功获取锁,启动调度器
            from .tasks import start_scheduler
            start_scheduler()
            
            # 注意: 不要关闭lock_fd或释放锁,保持锁直到进程结束
        except IOError:
            # 锁已被其他进程持有,跳过启动
            pass
