# Supabase 部署（5.0.0+）

## 1. 在 Supabase 建表

**方式 A — SQL 编辑器（推荐）**

1. 打开 [Supabase Dashboard](https://supabase.com/dashboard/project/yzhsrqjxzkadsvbzcbqz) → **SQL Editor**
2. 粘贴并执行仓库内 [`supabase/schema.sql`](../supabase/schema.sql) 的全部内容
3. 首次启动 App 时会自动写入种子食材与系统菜单（12 道）

**方式 B — 本地脚本**

```bash
pip install psycopg2-binary
# 在 .streamlit/secrets.toml 填好数据库连接后：
python scripts/init_supabase.py
```

## 2. Streamlit Cloud Secrets

在 [Streamlit Cloud](https://share.streamlit.io/) → 应用 → **Settings → Secrets** 添加：

```toml
SUPABASE_DB_HOST = "db.yzhsrqjxzkadsvbzcbqz.supabase.co"
SUPABASE_DB_PASSWORD = "你的数据库密码"
SUPABASE_DB_USER = "postgres"
SUPABASE_DB_NAME = "postgres"
SUPABASE_DB_PORT = "5432"

ADMIN_PASSWORD = "你的管理后台密码"
DEEPSEEK_API_KEY = "可选"
```

密码在 Supabase → **Project Settings → Database → Database password**（可 Reset）。

配置 Secrets 后，App 会：

- 使用 **昵称 + 4 位 PIN** 登录（多设备同账号）
- 菜单、今日餐单写入 Supabase
- **不再**使用 localStorage 跳转（无 vault 闪屏）

未配置 Supabase 时，仍回退到 4.x CSV + 浏览器备份模式。

## 3. 用户登录

- **新用户**：注册页 → 昵称、性别、年龄段、4 位 PIN
- **换设备**：登录页 → 相同昵称 + PIN

## 4. 管理员导出

管理后台 → 用户信息 / 菜单菜品 → **下载 CSV**。
