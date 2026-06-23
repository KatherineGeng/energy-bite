# Supabase 部署（5.0.0+）

## 1. 在 Supabase 建表

1. 打开 [SQL Editor](https://supabase.com/dashboard/project/yzhsrqjxzkadsvbzcbqz/sql/new)
2. 粘贴 [`schema.sql`](schema.sql) 全部内容
3. 出现 RLS 提示时选 **Run without RLS**（服务端直连，不用 anon key）

## 2. Streamlit Cloud Secrets（重要）

**Streamlit Cloud 不能稳定使用直连 `db.xxx.supabase.co:5432`**，必须用 **Transaction pooler（6543）**。

### 方式 A — 一整条 URI（推荐）

Supabase → **Project Settings → Database → Connection string** → 选 **Transaction pooler** → **URI**，复制整段：

```toml
SUPABASE_DB_URL = "postgresql://postgres.yzhsrqjxzkadsvbzcbqz:你的密码@aws-0-xxxxx.pooler.supabase.com:6543/postgres"

ADMIN_PASSWORD = "管理后台密码"
```

### 方式 B — 分开填写

```toml
SUPABASE_PROJECT_REF = "yzhsrqjxzkadsvbzcbqz"
SUPABASE_DB_POOLER_HOST = "aws-0-xxxxx.pooler.supabase.com"
SUPABASE_DB_POOLER_PORT = "6543"
SUPABASE_DB_USER = "postgres.yzhsrqjxzkadsvbzcbqz"
SUPABASE_DB_PASSWORD = "你的密码"
SUPABASE_DB_NAME = "postgres"
```

`POOLER_HOST` 和 URI 里的 region 以 Supabase 控制台显示的为准，不要猜。

密码：**Project Settings → Database → Database password**（可 Reset）。

## 3. 使用

- **注册**：昵称 + 性别 + 年龄 + 4 位 PIN  
- **登录**（换设备）：相同昵称 + PIN  
- 配置 Supabase 后不再走 localStorage 跳转  

## 4. 管理员

管理页 → 下载用户/菜单 **CSV**。
