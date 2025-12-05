# Role
You are a Senior Python Django Developer. Create a lightweight CRM system named `monsterabc_crm`.

# Project Structure
- **Root Directory**: `monsterabc_crm`
- **Project Config Package**: `monsterabc_crm`
- **App Name**: `sales`

# Tech Stack
- **Language**: Python 3.9+
- **Framework**: Django 4.2+
- **Database**: SQLite (Default)
- **Key Libraries**: 
  - `django-import-export` (Excel import/export)
  - `django-simple-captcha` (Login security)
  - `apscheduler` (Background tasks)
  - `requests` (WeCom notifications)
  - `openpyxl` (Excel driver)

# Requirements

## 1. Data Model (`sales/models.py`)
Create a `Customer` model:
- **Fields**:
  - `name`: CharField (Customer Name)
  - `phone`: CharField, Unique (Phone Number)
  - `sales_rep`: ForeignKey to User, Nullable. (Null = "High Seas/Public Pool"; Set = "Private Lead")
  - `status`: CharField choices: ['wait_contact', 'wait_visit', 'visited', 'signed', 'no_intent', 'unreachable']
  - `source`: CharField (Lead Source)
  - `city_auto`: CharField
  - `region_manual`: CharField
  - `contact_count`: PositiveIntegerField (default 0)
  - `next_contact_time`: DateTime (Nullable)
  - `created_at`: DateTime (Use `default=timezone.now` to allow importing historical timestamps)
  - `last_contact_at`: DateTime (Auto update on save)
  - `extra_data`: JSONField (default dict)
- **Meta**: Ordering by `-created_at`.

## 2. Admin & Import Logic (`sales/admin.py`)
- **Library**: Use `django-import-export`.
- **Resource Mapping**:
  - Define `CustomerResource` to map Chinese Excel headers to DB fields:
    - '姓名' -> `name`
    - '电话' -> `phone`
    - '线索创建时间' -> `created_at` (Format: `%Y-%m-%d %H:%M:%S`)
    - '线索渠道' -> `source`
    - '自动定位城市' -> `city_auto`
    - '手动填写地域' -> `region_manual`
- **Import Logic**:
  - Override `before_import_row` or `after_import_instance`.
  - If `request.user.is_superuser`: `sales_rep` remains None (goes to High Seas).
  - If regular staff: `sales_rep` = `request.user` (goes to My Customers).
- **Admin Classes**:
  - **MyCustomerAdmin**: Show items where `sales_rep` = current user.
  - **HighSeasAdmin**: (Use Proxy Model) Show items where `sales_rep` is None. Disable add/delete, allow "Claim" action.

## 3. Background Tasks (`sales/tasks.py` & `sales/apps.py`)
- **Scheduler**: Use `APScheduler`.
- **Task 1 (Every 1 min)**: Check if `next_contact_time` matches current time. Send mock WeCom Webhook request (print log if success).
- **Task 2 (Daily 02:00)**: Auto-recycle leads. 
  - Condition: `status='unreachable'` AND `last_contact_at` > 30 days ago AND `sales_rep` is not None.
  - Action: Set `sales_rep` to None (Move to High Seas).
- **Startup**: Initialize scheduler in `SalesConfig.ready()` ensuring it only runs once (`RUN_MAIN` check).

## 4. Frontend (`sales/views.py`, `sales/forms.py`, Templates)
- **Login**: `AuthenticationForm` extended with `CaptchaField`.
- **Dashboard**: 
  - Display "Today's Tasks" (next_contact_time is today).
  - Display "Tomorrow's Tasks".
  - Filter by logged-in user.
- **Templates**: Use **Bootstrap 5** CDN for styling. Clean, professional layout.

# Output Instructions
Generate the **full, working code** for the files below. Do not use placeholders.

1. `requirements.txt`
2. `monsterabc_crm/settings.py` (Configure `sales`, `import_export`, `captcha`; Set Language to 'zh-hans', Timezone to 'Asia/Shanghai')
3. `monsterabc_crm/urls.py` (Add admin, captcha, sales urls)
4. `sales/models.py`
5. `sales/admin.py` (Complete logic with Chinese header mapping)
6. `sales/tasks.py`
7. `sales/apps.py`
8. `sales/forms.py`
9. `sales/views.py`
10. `sales/templates/base.html` (Navbar, Bootstrap CSS)
11. `sales/templates/login.html`
12. `sales/templates/dashboard.html`


# 职位描述

您是一位资深的 Python Django 开发人员。请创建一个名为 `monsterabc_crm` 的轻量级 CRM 系统。

# 项目结构

- **根目录**: `monsterabc_crm`

- **项目配置包**: `monsterabc_crm`

- **应用名称**: `sales`

# 技术栈

- **语言**: Python 3.9+

- **框架**: Django 4.2+

- **数据库**: SQLite（默认）

- **关键库**:

- `django-import-export`（Excel 导入/导出）

- `django-simple-captcha`（登录安全）

- `apscheduler`（后台任务）

- `requests`（WeCom 通知）

- `openpyxl`（Excel 驱动程序）

# 要求

## 1. 数据模型 (`sales/models.py`)

创建 `Customer` 模型：

- **字段**:

- `name`: CharField（客户名称）

- `phone`: CharField，唯一（电话号码）

- `sales_rep`：指向用户的外键，可为空。 （Null = "公海/公共池"；Set = "私人线索")

- `status`: CharField 选项：['wait_contact', 'wait_visit', 'visited', 'signed', 'no_intent', 'unreachable']

- `source`: CharField（线索来源）

- `city_auto`: CharField

- `region_manual`: CharField

- `contact_count`: PositiveIntegerField（默认值 0）

- `next_contact_time`: DateTime（可为空）

- `created_at`: DateTime（使用 `default=timezone.now` 可导入历史时间戳）

- `last_contact_at`: DateTime（保存时自动更新）

- `extra_data`: JSONField（默认字典）

- **元数据**：按 `created_at` 排序。

## 2. 管理和导入逻辑 (`sales/admin.py`)
- **库**：使用 `django-import-export`。
- **资源映射**：
 - 定义“CustomerResource”以将中文 Excel 标题映射到数据库字段：
 -“姓名”->“姓名”
 -“电话”->“电话”
 - '线索创建时间' -> `created_at` (格式: `%Y-%m-%d %H:%M:%S`)
 - '线索渠道' -> '来源'
 - '自动定位城市' -> `city_auto`
 - '手动填写地域' -> `region_manual`
- **导入逻辑**：
 - 覆盖`before_import_row`或`after_import_instance`。 
- 如果 `request.user.is_superuser`：`sales_rep` 保持为 None（前往公海）。 
- 如果是正式员工：`sales_rep` = `request.user`（跳转到“我的客户”）。

- **管理员类**：

- **MyCustomerAdmin**：显示 `sales_rep` 等于当前用户的项目。

- **HighSeasAdmin**：（使用代理模型）显示 `sales_rep` 为 None 的项目。禁用添加/删除操作，允许“认领”操作。

## 3. 后台任务（`sales/tasks.py` 和 `sales/apps.py`）

- **调度器**：使用 `APScheduler`。

- **任务 1（每 1 分钟）**：检查 `next_contact_time` 是否与当前时间匹配。发送模拟 WeCom Webhook 请求（如果成功则打印日志）。

- **任务 2（每天 02:00）**：自动回收销售线索。 - 条件：`status='unreachable'` 且 `last_contact_at` > 30 天前 且 `sales_rep` 不为 None。

- 操作：将 `sales_rep` 设置为 None（移至公海）。

- **启动**：在 `SalesConfig.ready()` 中初始化调度程序，确保其仅运行一次（检查 `RUN_MAIN`）。

## 4. 前端（`sales/views.py`、`sales/forms.py`、模板）

- **登录**：扩展了带有 `CaptchaField` 的 `AuthenticationForm`。

- **仪表盘**：

- 显示“今日任务”（next_contact_time 为今天）。

- 显示“明日任务”。

- 按已登录用户筛选。

- **模板**：使用 **Bootstrap 5** CDN 进行样式设置。简洁专业的布局。

# 输出说明

请为以下文件生成**完整的、可运行的代码**。请勿使用占位符。

1. `requirements.txt`

2. `monsterabc_crm/settings.py`（配置 `sales`、`import_export` 和 `captcha`；设置语言为“zh-hans”，时区为“Asia/Shanghai”）

3. `monsterabc_crm/urls.py`（添加管理员、验证码和销售页面 URL）

4. `sales/models.py`

5. `sales/admin.py`（完善中文头部映射逻辑）

6. `sales/tasks.py`

7. `sales/apps.py`

8. `sales/forms.py`

9. `sales/views.py`

10. `sales/templates/base.html`（导航栏，Bootstrap CSS）

11. `sales/templates/login.html`

12. `sales/templates/dashboard.html`



mkdir monsterabc_crm

cd monsterabc_crm

python -m venv venv

# Windows 执行:

venv\Scripts\activate

# Mac/Linux 执行:

source venv/bin/activate

pip install django

# 注意：最后有一个点 "."，表示在当前目录创建，不要漏掉

django-admin startproject monsterabc_crm .

# 创建 app

python manage.py startapp sales



source venv/bin/activate && python manage.py runserver 0.0.0.0:3000

http://192.168.2.19:3000/
http://localhost:3000/
用户名"admin"和密码"admin123"登录