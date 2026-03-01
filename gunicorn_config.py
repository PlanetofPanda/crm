import multiprocessing

# 监听地址
bind = "127.0.0.1:9527"

# 工作进程数（推荐CPU核心数 * 2 + 1）
workers = 1

# 工作类型
worker_class = 'sync'

# 超时时间
timeout = 120

# 访问日志
accesslog = '/data/crm/log/gunicorn_access.log'
errorlog = '/data/crm/log/gunicorn_error.log'
loglevel = 'info'

# 进程名称
proc_name = 'monsterabc_crm'
