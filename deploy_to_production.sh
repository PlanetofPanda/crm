#!/bin/bash
# 生产服务器一键部署脚本
# 使用方法: ./deploy_to_production.sh

set -e  # 遇到错误立即退出

echo "========================================="
echo "  怪兽ABC CRM - 生产环境部署脚本"
echo "  修复: 管理员添加用户功能"
echo "========================================="
echo ""

# ===== 配置区域 - 请根据实际情况修改 =====
PROJECT_DIR="/data/crm"  # 项目目录（生产环境实际路径）
BACKUP_DIR="/var/backups/monsterabc_crm"  # 备份目录
SERVICE_NAME="crm"  # Supervisor服务名
# =========================================

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 检查是否在服务器上执行
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ 错误: 项目目录不存在: $PROJECT_DIR"
    echo "请在生产服务器上执行此脚本，或修改脚本中的 PROJECT_DIR 变量"
    exit 1
fi

cd $PROJECT_DIR

echo "📍 当前目录: $(pwd)"
echo ""

# 1. 备份数据库
echo "📦 [1/6] 备份数据库..."
mkdir -p $BACKUP_DIR
if [ -f "db.sqlite3" ]; then
    cp db.sqlite3 $BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3
    echo "✅ 数据库已备份: $BACKUP_DIR/db_backup_$TIMESTAMP.sqlite3"
else
    echo "⚠️  警告: 未找到 db.sqlite3 文件"
fi
echo ""

# 2. 备份代码文件
echo "📦 [2/6] 备份代码文件..."
if [ -f "sales/forms.py" ]; then
    cp sales/forms.py sales/forms.py.backup.$TIMESTAMP
    echo "✅ 代码已备份: sales/forms.py.backup.$TIMESTAMP"
else
    echo "❌ 错误: 未找到 sales/forms.py 文件"
    exit 1
fi
echo ""

# 3. 拉取最新代码
echo "🔄 [3/6] 拉取最新代码..."
if [ -d ".git" ]; then
    git fetch --all
    echo "当前分支: $(git branch --show-current)"
    echo "最新提交："
    git log -1 --oneline
    echo ""
    read -p "确认拉取最新代码? (y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        # 获取当前分支名
        CURRENT_BRANCH=$(git branch --show-current)
        echo "正在拉取分支: $CURRENT_BRANCH"
        git pull origin $CURRENT_BRANCH
        echo "✅ 代码更新成功"
    else
        echo "⚠️  已取消代码更新"
    fi
else
    echo "⚠️  警告: 不是 Git 仓库，跳过代码拉取"
    echo "请手动更新 sales/forms.py 文件"
fi
echo ""

# 4. 检查修改
echo "🔍 [4/6] 检查文件修改..."
if grep -q "def save(self, commit=True):" sales/forms.py; then
    echo "✅ 确认: save() 方法已存在于 UserManagementForm"
    echo "修复代码已就位！"
else
    echo "❌ 警告: 未找到 save() 方法"
    echo "请检查 sales/forms.py 文件是否正确更新"
    read -p "是否继续部署? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "已取消部署"
        exit 1
    fi
fi
echo ""

# 5. 重启应用
echo "🔄 [5/6] 重启应用..."

# 尝试不同的重启方法
if command -v supervisorctl &> /dev/null; then
    echo "使用 Supervisor 重启..."
    sudo supervisorctl restart $SERVICE_NAME
    sleep 2
    sudo supervisorctl status $SERVICE_NAME
    echo "✅ 应用已通过 Supervisor 重启"
elif systemctl list-units | grep -q gunicorn; then
    echo "使用 systemd 重启..."
    sudo systemctl restart gunicorn
    sudo systemctl status gunicorn --no-pager
    echo "✅ 应用已通过 systemd 重启"
else
    echo "⚠️  未检测到 Supervisor 或 systemd"
    echo "请手动重启应用"
    echo ""
    echo "可能的重启命令："
    echo "  - sudo supervisorctl restart $SERVICE_NAME"
    echo "  - sudo systemctl restart gunicorn"
    echo "  - pkill -HUP gunicorn"
fi
echo ""

# 6. 验证服务状态
echo "🔍 [6/6] 验证服务状态..."
sleep 2

# 检查端口9527
if netstat -tlnp 2>/dev/null | grep -q ":9527"; then
    echo "✅ 端口 9527 正在监听"
elif lsof -i :9527 2>/dev/null | grep -q LISTEN; then
    echo "✅ 端口 9527 正在监听"
else
    echo "⚠️  警告: 端口 9527 未在监听"
    echo "请检查应用是否正常启动"
fi

# 检查进程
if ps aux | grep -v grep | grep -q "gunicorn.*monsterabc_crm"; then
    echo "✅ Gunicorn 进程正在运行"
    echo ""
    echo "进程信息:"
    ps aux | grep -v grep | grep "gunicorn.*monsterabc_crm" | head -3
else
    echo "⚠️  警告: 未找到 Gunicorn 进程"
fi
echo ""

echo "========================================="
echo "  部署完成！"
echo "========================================="
echo ""
echo "📊 部署摘要:"
echo "  - 备份位置: $BACKUP_DIR/"
echo "  - 数据库备份: db_backup_$TIMESTAMP.sqlite3"
echo "  - 代码备份: sales/forms.py.backup.$TIMESTAMP"
echo ""
echo "🧪 下一步操作:"
echo "  1. 访问生产环境测试功能"
echo "  2. 登录管理员账号"
echo "  3. 进入系统设置 → 添加用户"
echo "  4. 验证新用户是否能成功创建"
echo ""
echo "📝 查看日志命令:"
echo "  tail -f /var/log/monsterabc_crm/gunicorn_error.log"
echo ""
echo "🔙 如需回滚:"
echo "  cp sales/forms.py.backup.$TIMESTAMP sales/forms.py"
echo "  sudo supervisorctl restart $SERVICE_NAME"
echo ""
echo "========================================="
