from .settings import *

# 生产环境特定配置
DEBUG = False

# 允许所有主机（或者修改为您的实际域名/IP，如 ['your-domain.com', '47.xc.xx.xx']）
ALLOWED_HOSTS = ['*']

# 静态文件配置（确保收集静态文件时路径正确）
STATIC_ROOT = BASE_DIR / "staticfiles"
