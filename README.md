# Personal Access Token (PAT) 權限控管系統

一個類似 GitHub Fine-grained Personal Access Tokens 的權限控管系統，使用 FastAPI 實作，支援階層式權限管理和完整的審計日誌。

## 🎯 專案特色

- **JWT 認證系統**：安全的使用者登入與 Session Token 管理
- **Personal Access Token (PAT)**：類似 GitHub 的細粒度存取令牌
- **階層式權限控制**：高階權限自動包含低階權限，但不跨資源繼承
- **完整的審計日誌**：記錄每次 Token 使用情況
- **FCS 檔案處理**：支援流式細胞儀資料分析
- **Rate Limiting**：基於 IP 的請求速率限制
- **Docker 容器化**：一鍵啟動完整環境

## 📋 技術棧

- **框架**: FastAPI 0.109.0
- **資料庫**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **遷移工具**: Alembic
- **認證**: JWT (python-jose)
- **密碼加密**: bcrypt
- **FCS 處理**: flowio
- **容器化**: Docker + Docker Compose
- **測試**: pytest

## 🏗️ 架構說明

### 目錄結構

```
pat-auth-system/
├── docker-compose.yml          # Docker Compose 配置
├── Dockerfile                  # Docker 映像檔
├── requirements.txt            # Python 依賴
├── alembic.ini                # Alembic 配置
├── alembic/                   # 資料庫遷移
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── app/
│   ├── main.py                # FastAPI 應用程式入口
│   ├── config.py              # 配置管理
│   ├── database.py            # 資料庫連接
│   ├── models/                # SQLAlchemy 模型
│   │   ├── user.py
│   │   ├── token.py
│   │   ├── audit_log.py
│   │   └── fcs_file.py
│   ├── schemas/               # Pydantic 模型
│   │   ├── common.py
│   │   ├── user.py
│   │   ├── token.py
│   │   ├── audit_log.py
│   │   └── fcs.py
│   ├── routers/               # API 路由
│   │   ├── auth.py
│   │   ├── tokens.py
│   │   ├── workspaces.py
│   │   ├── users.py
│   │   └── fcs.py
│   ├── services/              # 業務邏輯
│   │   ├── user_service.py
│   │   ├── token_service.py
│   │   ├── audit_service.py
│   │   └── fcs_service.py
│   ├── core/                  # 核心功能
│   │   ├── security.py
│   │   └── permissions.py
│   ├── dependencies/          # FastAPI 依賴
│   │   └── auth.py
│   └── middleware/            # 中間件
│       └── rate_limit.py
├── tests/                     # 測試
│   └── test_permissions.py
└── data/                      # 資料檔案
    └── 0000123456_1234567_AML_ClearLLab10C_TTube.fcs
```

### 權限階層設計

系統支援三種資源的階層式權限：

| 資源 | 權限階層（高 → 低） | 說明 |
|------|---------------------|------|
| `workspaces` | admin > delete > write > read | 工作區管理權限 |
| `users` | write > read | 使用者資訊權限 |
| `fcs` | analyze > write > read | FCS 檔案操作權限 |

**重要規則**：
- 高階權限自動包含所有低階權限（同資源內）
- 權限**不會**跨資源繼承
- 例如：`workspaces:admin` 包含 `workspaces:read/write/delete`，但不包含 `fcs:read`

### Token 安全機制

1. **Token 格式**: `pat_` + 64 位隨機十六進位字串
2. **儲存方式**:
   - 完整 Token：僅在建立時回傳一次
   - 資料庫儲存：SHA-256 雜湊 + 前 12 字元作為檢索前綴
   - 顯示格式：僅顯示前 12 字元（`pat_a1b2c3d4`）
3. **驗證流程**:
   - 使用前綴快速定位候選 Token
   - 使用雜湊驗證完整性
   - 檢查過期時間和撤銷狀態

## 🚀 快速開始

### 前置需求

- Docker 20.10+
- Docker Compose 2.0+

### 一鍵啟動

```bash
# 1. Clone 專案
git clone https://github.com/yourusername/pat-auth-system.git
cd pat-auth-system

# 2. 啟動服務（自動執行 migration）
docker-compose up -d

# 3. 查看日誌
docker-compose logs -f api

# 4. 等待服務啟動完成
# API 將在 http://localhost:8000 啟動
# API 文件在 http://localhost:8000/docs
```

### 停止服務

```bash
docker-compose down

# 如需刪除資料庫
docker-compose down -v
```

## 📚 API 使用範例

### 1. 註冊使用者

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "email": "demo@example.com",
    "password": "password123"
  }'
```

### 2. 登入取得 JWT

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "demo_user",
    "password": "password123"
  }'

# 回應範例
{
  "success": true,
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "user": {...}
  }
}
```

### 3. 建立 Personal Access Token

```bash
JWT_TOKEN="your_jwt_token_here"

curl -X POST "http://localhost:8000/api/v1/tokens" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "FCS Analysis Token",
    "scopes": ["fcs:analyze"],
    "expires_in_days": 90
  }'

# 回應範例
{
  "success": true,
  "data": {
    "id": "abc123...",
    "name": "FCS Analysis Token",
    "token": "pat_a1b2c3d4e5f6...",  # 完整 Token，僅此一次顯示
    "scopes": ["fcs:analyze"],
    "created_at": "2024-01-15T10:00:00Z",
    "expires_at": "2024-04-15T10:00:00Z"
  }
}
```

### 4. 使用 PAT 存取受保護資源

```bash
PAT_TOKEN="pat_a1b2c3d4e5f6..."

# 取得 FCS 參數資訊
curl -X GET "http://localhost:8000/api/v1/fcs/parameters" \
  -H "Authorization: Bearer $PAT_TOKEN"

# 取得 FCS 事件資料
curl -X GET "http://localhost:8000/api/v1/fcs/events?limit=10&offset=0" \
  -H "Authorization: Bearer $PAT_TOKEN"

# 取得統計分析
curl -X GET "http://localhost:8000/api/v1/fcs/statistics" \
  -H "Authorization: Bearer $PAT_TOKEN"
```

### 5. 查看 Token 使用日誌

```bash
TOKEN_ID="abc123..."

curl -X GET "http://localhost:8000/api/v1/tokens/$TOKEN_ID/logs" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### 6. 撤銷 Token

```bash
curl -X DELETE "http://localhost:8000/api/v1/tokens/$TOKEN_ID" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## 🧪 執行測試

```bash
# 在容器內執行測試
docker-compose exec api pytest

# 執行特定測試
docker-compose exec api pytest tests/test_permissions.py -v

# 執行並顯示覆蓋率
docker-compose exec api pytest --cov=app tests/
```

### 必要測試案例

系統包含三個關鍵測試：

1. **權限階層繼承驗證** (`test_permission_hierarchy_inheritance`)
   - 驗證高階權限包含低階權限
   - 驗證權限不跨資源繼承

2. **Token 過期與撤銷處理** (`test_token_expiry_and_revocation`)
   - 區分過期和撤銷的錯誤訊息
   - 驗證兩種狀態的處理邏輯

3. **Token 安全儲存驗證** (`test_token_security_storage`)
   - 驗證資料庫無明文 Token
   - 驗證前綴和雜湊儲存
   - 驗證錯誤 Token 無法通過驗證

## 🎨 設計決策

### 1. 為什麼使用前綴 + 雜湊的方式？

- **效能考量**：使用前綴可以快速縮小搜尋範圍，避免對所有 Token 進行雜湊比對
- **安全性**：完整 Token 以 SHA-256 雜湊儲存，即使資料庫洩漏也無法還原原始 Token
- **可用性**：前綴可用於日誌顯示和使用者識別，無需揭露完整 Token

### 2. 為什麼權限不跨資源繼承？

- **最小權限原則**：避免過度授權，每個資源的權限應該明確授予
- **安全性**：防止意外的權限提升
- **清晰性**：使用者可以清楚知道每個 Token 的確切權限範圍

### 3. 為什麼使用審計日誌？

- **安全追蹤**：記錄所有 Token 使用情況，便於安全審計
- **問題排查**：當權限問題發生時，可以追溯歷史記錄
- **合規要求**：許多產業需要完整的存取記錄

### 4. JWT vs PAT 的設計考量

- **JWT**：短期（30分鐘）Session Token，用於互動式操作
- **PAT**：長期（30-365天）Access Token，用於自動化和 API 存取
- 兩者分離可以平衡安全性和便利性

## 📊 資料庫模型

### Users
- `id`: 使用者唯一識別碼
- `username`: 使用者名稱（唯一）
- `email`: 電子郵件（唯一）
- `hashed_password`: 密碼雜湊
- `created_at`, `updated_at`: 時間戳記

### Tokens
- `id`: Token 唯一識別碼
- `user_id`: 所屬使用者
- `name`: Token 名稱
- `token_prefix`: Token 前 12 字元（用於快速查找）
- `token_hash`: Token SHA-256 雜湊
- `scopes`: JSON 格式的權限列表
- `is_revoked`: 是否已撤銷
- `created_at`: 建立時間
- `expires_at`: 到期時間
- `last_used_at`: 最後使用時間

### AuditLogs
- `id`: 日誌唯一識別碼
- `token_id`: 使用的 Token
- `timestamp`: 時間戳記
- `ip_address`: 來源 IP
- `method`: HTTP 方法
- `endpoint`: API 端點
- `status_code`: 回應狀態碼
- `authorized`: 是否授權成功
- `reason`: 失敗原因（如果有）

### FCSFiles
- `id`: 檔案唯一識別碼
- `user_id`: 上傳使用者
- `filename`: 檔案名稱
- `file_path`: 檔案路徑
- `total_events`: 事件總數
- `total_parameters`: 參數總數
- `created_at`: 上傳時間

## 🔧 環境變數配置

複製 `.env.example` 為 `.env` 並修改：

```bash
# 資料庫連接
DATABASE_URL=postgresql://pat_user:pat_password@db:5432/pat_db

# JWT 設定（請務必修改為安全的密鑰）
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Token 設定
TOKEN_PREFIX=pat_
TOKEN_LENGTH=32
TOKEN_PREFIX_DISPLAY_LENGTH=8

# FCS 檔案
DEFAULT_FCS_FILE=data/0000123456_1234567_AML_ClearLLab10C_TTube.fcs
```

## 📝 API 端點總覽

### 認證 (Authentication)
- `POST /api/v1/auth/register` - 註冊新使用者
- `POST /api/v1/auth/login` - 登入取得 JWT

### Token 管理 (需 JWT)
- `POST /api/v1/tokens` - 建立 PAT
- `GET /api/v1/tokens` - 列出所有 PAT
- `GET /api/v1/tokens/{id}` - 取得單一 PAT 詳情
- `DELETE /api/v1/tokens/{id}` - 撤銷 PAT
- `GET /api/v1/tokens/{id}/logs` - 取得 PAT 使用日誌

### Workspaces (需 PAT，Stub 實作)
- `GET /api/v1/workspaces` - 列出工作區 (`workspaces:read`)
- `POST /api/v1/workspaces` - 建立工作區 (`workspaces:write`)
- `DELETE /api/v1/workspaces/{id}` - 刪除工作區 (`workspaces:delete`)
- `PUT /api/v1/workspaces/{id}/settings` - 更新設定 (`workspaces:admin`)

### Users (需 PAT，Stub 實作)
- `GET /api/v1/users/me` - 取得當前使用者資訊 (`users:read`)
- `PUT /api/v1/users/me` - 更新當前使用者資訊 (`users:write`)

### FCS Data (需 PAT，實際實作)
- `GET /api/v1/fcs/parameters` - 列出 FCS 參數 (`fcs:read`)
- `GET /api/v1/fcs/events` - 取得 FCS 事件資料 (`fcs:read`)
- `POST /api/v1/fcs/upload` - 上傳 FCS 檔案 (`fcs:write`)
- `GET /api/v1/fcs/statistics` - 取得統計分析 (`fcs:analyze`)

## 🐛 疑難排解

### 問題 1: 無法連接資料庫

```bash
# 檢查資料庫服務狀態
docker-compose ps

# 重啟資料庫
docker-compose restart db

# 檢查資料庫日誌
docker-compose logs db
```

### 問題 2: Migration 失敗

```bash
# 手動執行 migration
docker-compose exec api alembic upgrade head

# 查看當前版本
docker-compose exec api alembic current

# 查看 migration 歷史
docker-compose exec api alembic history
```

### 問題 3: FCS 檔案無法讀取

```bash
# 確認檔案存在
docker-compose exec api ls -la data/

# 檢查檔案權限
docker-compose exec api ls -l data/0000123456_1234567_AML_ClearLLab10C_TTube.fcs
```

## 📈 效能考量

- 使用前綴索引加速 Token 查找
- 資料庫連接池管理
- Rate Limiting 防止濫用
- 審計日誌定期歸檔（建議實作）

## 🔐 安全建議

1. **生產環境必做**：
   - 更改 `SECRET_KEY` 為強隨機字串
   - 使用 HTTPS
   - 啟用資料庫 SSL 連接
   - 定期備份資料庫
   - 實作 Token 使用次數限制

2. **建議實作**：
   - IP 白名單限制
   - Token 使用次數統計
   - 異常行為檢測
   - 定期清理過期 Token

## 👥 作者

Your Name - [your.email@example.com](mailto:your.email@example.com)

## 📄 授權

MIT License

## 🙏 致謝

- FastAPI 團隊提供優秀的框架
- FlowIO 專案提供 FCS 檔案解析功能
- GitHub 的 Fine-grained PAT 設計啟發

---

**完整 API 文件**: http://localhost:8000/docs

**技術支援**: 請提交 Issue 到 GitHub Repository
