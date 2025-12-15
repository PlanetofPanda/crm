#!/bin/bash
# 修复运行环境并重启服务

echo "🔄 开始修复运行环境..."

# 1. 删除旧的/损坏的虚拟环境
if [ -d "venv" ]; then
    echo "正在移除旧的虚拟环境..."
    rm -rf venv
fi

# 2. 重新创建虚拟环境
echo "创建新的虚拟环境..."
python3 -m venv venv

# 3. 激活并安装依赖
echo "安装依赖包..."
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn

# 4. 修复 start.sh (确保使用相对路径)
echo "./venv/bin/gunicorn --bind 0.0.0.0:9527 monsterabc_crm.wsgi:application" > start.sh

# 5. 重启服务
echo "🔄 重启服务..."
pkill -f gunicorn
sh start.sh

echo "✅ 修复完成！请刷新浏览器查看。"
