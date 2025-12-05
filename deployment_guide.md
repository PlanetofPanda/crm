# 怪兽ABC CRM 生产环境部署指南

本文档提供详细的生产环境部署步骤和数据备份策略。

## 一、生产环境准备

### 1.1 服务器要求

**推荐配置：**
- **操作系统**: Ubuntu 20.04 LTS 或 CentOS 8+
- **CPU**: 2核心
- **内存**: 2GB RAM
- **磁盘**: 20GB SSD
- **Python**: 3.8+

### 1.2 安装系统依赖

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# CentOS/RHEL
sudo yum install python3 python3-pip nginx supervisor -y
```

---

## 二、项目部署

### 2.1 克隆或上传项目

```bash
# 创建项目目录
sudo mkdir -p /var/www/monsterabc_crm
sudo chown $USER:$USER /var/www/monsterabc_crm

# 上传项目文件到服务器
# 方式1: 使用Git
cd /var/www/monsterabc_crm
git clone <your-repo-url> .

# 方式2: 使用SCP上传
# scp -r /path/to/local/monsterabc_crm user@server:/var/www/
```

### 2.2 创建虚拟环境并安装依赖

```bash
cd /var/www/monsterabc_crm

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级pip
pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt

# 安装生产环境所需的额外包
pip install gunicorn
```

### 2.3 配置生产环境设置

创建生产环境配置文件 `monsterabc_crm/settings_production.py`:

```python
from .settings import *

# 生产环境配置
DEBUG = False

# 设置允许的主机（替换为实际域名或IP）
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com', 'SERVER_IP']

# 安全设置
SECRET_KEY = 'your-production-secret-key-here-change-this'  # 使用强随机密钥

# HTTPS相关（如果使用SSL）
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# 静态文件配置
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# 数据库（生产环境建议使用PostgreSQL或MySQL）
# 如继续使用SQLite:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 如果使用PostgreSQL（推荐）:
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'monsterabc_crm',
#         'USER': 'your_db_user',
#         'PASSWORD': 'your_db_password',
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }
```

生成新的SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 2.4 数据库迁移和静态文件收集

```bash
# 使用生产环境配置
export DJANGO_SETTINGS_MODULE=monsterabc_crm.settings_production

# 执行数据库迁移
python manage.py migrate

# 收集静态文件
python manage.py collectstatic --noinput

# 创建超级管理员（如果需要）
python manage.py createsuperuser
```

---

## 三、使用Gunicorn运行应用

### 3.1 测试Gunicorn

```bash
cd /var/www/monsterabc_crm
source venv/bin/activate

# 测试运行
gunicorn --bind 0.0.0.0:8000 monsterabc_crm.wsgi:application
```

### 3.2 创建Gunicorn配置文件

创建 `/var/www/monsterabc_crm/gunicorn_config.py`:

```python
import multiprocessing

# 监听地址
bind = "127.0.0.1:8000"

# 工作进程数（推荐CPU核心数 * 2 + 1）
workers = multiprocessing.cpu_count() * 2 + 1

# 工作类型
worker_class = 'sync'

# 超时时间
timeout = 120

# 访问日志
accesslog = '/var/log/monsterabc_crm/gunicorn_access.log'
errorlog = '/var/log/monsterabc_crm/gunicorn_error.log'
loglevel = 'info'

# 进程名称
proc_name = 'monsterabc_crm'
```

创建日志目录:

```bash
sudo mkdir -p /var/log/monsterabc_crm
sudo chown $USER:$USER /var/log/monsterabc_crm
```

---

## 四、配置Nginx反向代理

### 4.1 创建Nginx配置文件

创建 `/etc/nginx/sites-available/monsterabc_crm`:

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # 日志文件
    access_log /var/log/nginx/monsterabc_crm_access.log;
    error_log /var/log/nginx/monsterabc_crm_error.log;

    # 静态文件
    location /static/ {
        alias /var/www/monsterabc_crm/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 代理到Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 120;
        proxy_send_timeout 120;
        proxy_read_timeout 120;
    }

    # 文件上传大小限制
    client_max_body_size 10M;
}
```

### 4.2 启用配置并测试

```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/monsterabc_crm /etc/nginx/sites-enabled/

# 测试Nginx配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

---

## 五、使用Supervisor管理进程

### 5.1 创建Supervisor配置

创建 `/etc/supervisor/conf.d/monsterabc_crm.conf`:

```ini
[program:monsterabc_crm]
command=/var/www/monsterabc_crm/venv/bin/gunicorn -c /var/www/monsterabc_crm/gunicorn_config.py monsterabc_crm.wsgi:application
directory=/var/www/monsterabc_crm
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/monsterabc_crm/supervisor.log
environment=DJANGO_SETTINGS_MODULE="monsterabc_crm.settings_production"
```

### 5.2 启动和管理服务

```bash
# 重新加载Supervisor配置
sudo supervisorctl reread
sudo supervisorctl update

# 启动应用
sudo supervisorctl start monsterabc_crm

# 其他管理命令
sudo supervisorctl stop monsterabc_crm      # 停止
sudo supervisorctl restart monsterabc_crm   # 重启
sudo supervisorctl status monsterabc_crm    # 查看状态
```

---

## 六、数据库备份策略

### 6.1 手动备份

#### SQLite备份

```bash
#!/bin/bash
# 备份SQLite数据库

BACKUP_DIR="/var/backups/monsterabc_crm"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_PATH="/var/www/monsterabc_crm/db.sqlite3"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp $DB_PATH $BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3

# 压缩备份
gzip $BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3

echo "Database backup completed: db_backup_$TIMESTAMP.sqlite3.gz"
```

#### PostgreSQL备份（如使用）

```bash
#!/bin/bash
# 备份PostgreSQL数据库

BACKUP_DIR="/var/backups/monsterabc_crm"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_NAME="monsterabc_crm"
DB_USER="your_db_user"

mkdir -p $BACKUP_DIR

# 导出数据库
pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_backup_$TIMESTAMP.sql.gz

echo "Database backup completed: db_backup_$TIMESTAMP.sql.gz"
```

### 6.2 自动定时备份

#### 方式1: 使用Cron（推荐）

1. **创建备份脚本** `/var/www/monsterabc_crm/backup.sh`:

```bash
#!/bin/bash

# 配置
BACKUP_DIR="/var/backups/monsterabc_crm"
DB_PATH="/var/www/monsterabc_crm/db.sqlite3"
RETENTION_DAYS=30  # 保留30天的备份
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp $DB_PATH $BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3
gzip $BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3

# 删除超过保留期限的备份
find $BACKUP_DIR -name "db_backup_*.sqlite3.gz" -mtime +$RETENTION_DAYS -delete

# 记录日志
echo "$(date): Database backup completed - db_backup_$TIMESTAMP.sqlite3.gz" >> /var/log/monsterabc_crm/backup.log

# 输出备份文件大小
du -h $BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3.gz
```

2. **设置脚本权限**:

```bash
chmod +x /var/www/monsterabc_crm/backup.sh
```

3. **配置Cron定时任务**:

```bash
# 编辑crontab
crontab -e

# 添加以下行（每天凌晨2点执行备份）
0 2 * * * /var/www/monsterabc_crm/backup.sh
```

**常用Cron时间配置：**
- `0 2 * * *` - 每天凌晨2点
- `0 */6 * * *` - 每6小时
- `0 2 * * 0` - 每周日凌晨2点
- `0 2 1 * *` - 每月1号凌晨2点

#### 方式2: 使用Django管理命令

1. **创建自定义管理命令** `sales/management/commands/backup_database.py`:

```python
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import shutil
from datetime import datetime, timedelta
import gzip

class Command(BaseCommand):
    help = '备份数据库'

    def handle(self, *args, **options):
        backup_dir = '/var/backups/monsterabc_crm'
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        db_path = settings.DATABASES['default']['NAME']
        
        # 备份文件名
        backup_file = os.path.join(backup_dir, f'db_backup_{timestamp}.sqlite3')
        
        # 复制数据库文件
        shutil.copy2(db_path, backup_file)
        
        # 压缩
        with open(backup_file, 'rb') as f_in:
            with gzip.open(f'{backup_file}.gz', 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 删除未压缩文件
        os.remove(backup_file)
        
        # 清理30天前的备份
        retention_days = 30
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        for filename in os.listdir(backup_dir):
            if filename.startswith('db_backup_') and filename.endswith('.gz'):
                file_path = os.path.join(backup_dir, filename)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
                    self.stdout.write(f'Deleted old backup: {filename}')
        
        self.stdout.write(self.style.SUCCESS(
            f'Database backup completed: db_backup_{timestamp}.sqlite3.gz'
        ))
```

2. **在Cron中调用Django命令**:

```bash
0 2 * * * cd /var/www/monsterabc_crm && /var/www/monsterabc_crm/venv/bin/python manage.py backup_database
```

### 6.3 异地备份（推荐）

将备份文件同步到远程服务器或云存储：

```bash
#!/bin/bash
# 同步备份到远程服务器

BACKUP_DIR="/var/backups/monsterabc_crm"
REMOTE_USER="backup_user"
REMOTE_HOST="backup.server.com"
REMOTE_DIR="/backups/monsterabc_crm"

# 使用rsync同步
rsync -avz --delete $BACKUP_DIR/ $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/

# 或使用阿里云OSS（需要安装ossutil）
# ossutil cp -r $BACKUP_DIR oss://your-bucket/monsterabc_crm/
```

---

## 七、数据恢复

### 7.1 从SQLite备份恢复

```bash
#!/bin/bash
# 恢复SQLite数据库

BACKUP_FILE="/var/backups/monsterabc_crm/db_backup_20250123_020000.sqlite3.gz"
DB_PATH="/var/www/monsterabc_crm/db.sqlite3"

# 停止应用
sudo supervisorctl stop monsterabc_crm

# 备份当前数据库（以防万一）
cp $DB_PATH $DB_PATH.before_restore

# 解压并恢复
gunzip -c $BACKUP_FILE > $DB_PATH

# 重启应用
sudo supervisorctl start monsterabc_crm

echo "Database restored from: $BACKUP_FILE"
```

### 7.2 从PostgreSQL备份恢复

```bash
#!/bin/bash
# 恢复PostgreSQL数据库

BACKUP_FILE="/var/backups/monsterabc_crm/db_backup_20250123_020000.sql.gz"
DB_NAME="monsterabc_crm"
DB_USER="your_db_user"

# 停止应用
sudo supervisorctl stop monsterabc_crm

# 删除现有数据库并重建
dropdb -U $DB_USER $DB_NAME
createdb -U $DB_USER $DB_NAME

# 恢复数据
gunzip -c $BACKUP_FILE | psql -U $DB_USER $DB_NAME

# 重启应用
sudo supervisorctl start monsterabc_crm

echo "Database restored from: $BACKUP_FILE"
```

---

## 八、安全加固建议

### 8.1 配置防火墙

```bash
# Ubuntu UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable

# CentOS Firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload
```

### 8.2 配置SSL证书（Let's Encrypt）

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取SSL证书
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 8.3 其他安全措施

- 更改默认SSH端口
- 禁用root直接登录
- 配置fail2ban防止暴力破解
- 定期更新系统和依赖包
- 使用强密码策略

---

## 九、监控与维护

### 9.1 日志查看

```bash
# Gunicorn日志
tail -f /var/log/monsterabc_crm/gunicorn_access.log
tail -f /var/log/monsterabc_crm/gunicorn_error.log

# Nginx日志
tail -f /var/log/nginx/monsterabc_crm_access.log
tail -f /var/log/nginx/monsterabc_crm_error.log

# Supervisor日志
tail -f /var/log/monsterabc_crm/supervisor.log
```

### 9.2 磁盘空间监控

创建 `/var/www/monsterabc_crm/check_disk.sh`:

```bash
#!/bin/bash

THRESHOLD=80
CURRENT=$(df / | grep / | awk '{ print $5}' | sed 's/%//g')

if [ "$CURRENT" -gt "$THRESHOLD" ]; then
    echo "WARNING: Disk usage is ${CURRENT}%"
    # 可以发送邮件或企业微信通知
fi
```

---

## 十、更新和维护流程

### 10.1 代码更新流程

```bash
# 1. 备份数据库
/var/www/monsterabc_crm/backup.sh

# 2. 拉取最新代码
cd /var/www/monsterabc_crm
git pull origin main

# 3. 激活虚拟环境
source venv/bin/activate

# 4. 更新依赖
pip install -r requirements.txt

# 5. 迁移数据库
python manage.py migrate

# 6. 收集静态文件
python manage.py collectstatic --noinput

# 7. 重启应用
sudo supervisorctl restart monsterabc_crm
```

---

## 附录：快速部署检查清单

- [ ] 服务器环境准备完成
- [ ] 项目代码上传
- [ ] 虚拟环境创建并安装依赖
- [ ] 生产环境配置文件已修改
- [ ] SECRET_KEY已更换
- [ ] ALLOWED_HOSTS已配置
- [ ] 数据库迁移完成
- [ ] 静态文件收集完成
- [ ] Gunicorn配置完成
- [ ] Nginx配置完成
- [ ] Supervisor配置完成
- [ ] 防火墙规则配置
- [ ] SSL证书安装（如需要）
- [ ] 自动备份脚本配置
- [ ] Cron定时任务设置
- [ ] 监控和告警配置
- [ ] 应用功能测试

---

**部署完成后请访问：**
- HTTP: `http://your-domain.com`
- HTTPS: `https://your-domain.com`

**常用维护命令：**
```bash
# 查看应用状态
sudo supervisorctl status monsterabc_crm

# 重启应用
sudo supervisorctl restart monsterabc_crm

# 查看日志
tail -f /var/log/monsterabc_crm/gunicorn_error.log

# 手动备份
/var/www/monsterabc_crm/backup.sh
```
