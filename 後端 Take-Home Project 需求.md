# Python 後端 Take-Home Project 需求

## 🎯 專案目標

設計並實作一個 **Personal Access Token (PAT) 權限控管系統**，類似 GitHub 的 Fine-grained Personal Access Tokens 機制。

---

## 📋 專案需求

### 核心功能

**1. 認證流程**

```
┌─────────────────────────────────────────────────────────┐
│  1. 使用者登入 → 取得 JWT Session Token                  │
│  2. 使用 JWT 呼叫 /tokens API → 建立 PAT                │
│  3. 使用 PAT 呼叫受保護資源 → 依 scopes 授權             │
└─────────────────────────────────────────────────────────┘
```

**2. Token 管理**

- 使用者可建立、列出、撤銷 Personal Access Tokens
- Token 屬性：唯一識別碼、名稱、建立/到期時間、最後使用時間、權限範圍
- 到期時間選項：30天、90天、1年、自訂
- Token 格式：`pat_` 前綴 + 隨機字串（例：`pat_a1b2c3d4e5f6...`）

**3. 權限控制（全域權限，階層式結構）**

| 資源 | 權限階層（高 → 低） |
|------|---------------------|
| `workspacess` | admin > delete > write > read |
| `users` | write > read |
| `fcs` | analyze > write > read |

**規則**：高階權限自動包含低階權限，但不跨資源繼承。

**4. Token Audit Log（必要功能）**

記錄每次 PAT 使用紀錄，包含：
- Token ID（不記錄完整 Token）
- 呼叫時間
- 來源 IP
- 請求端點與方法
- 回應狀態碼
- 是否授權成功

**5. 安全性要求**

| 項目 | 規格 |
|------|------|
| Token 儲存 | SHA-256 雜湊 + 前 8 字元明文作為檢索前綴 |
| Token 顯示 | 僅在建立時顯示一次完整內容 |
| Rate Limiting | 基於 IP，每分鐘 60 次請求 |
| 密碼儲存 | bcrypt 或 argon2 |

---

### API 端點設計

**認證（帳號密碼）**
```
POST   /api/v1/auth/register     # 註冊
POST   /api/v1/auth/login        # 登入，回傳 JWT
```

**Token 管理（需 JWT）**
```
POST   /api/v1/tokens            # 建立 PAT（回傳完整 Token，僅此一次）
GET    /api/v1/tokens            # 列出所有 PAT（僅顯示 prefix）
GET    /api/v1/tokens/{id}       # 取得單一 PAT
DELETE /api/v1/tokens/{id}       # 撤銷 PAT
GET    /api/v1/tokens/{id}/logs  # 取得該 Token 的 Audit Log
```

**受保護資源（需 PAT）**

```
# workspacess（Stub 實作）
GET    /api/v1/workspacess                   # workspacess:read
POST   /api/v1/workspacess                   # workspacess:write
DELETE /api/v1/workspacess/{id}              # workspacess:delete
PUT    /api/v1/workspacess/{id}/settings     # workspacess:admin

# Users（Stub 實作）
GET    /api/v1/users/me                    # users:read
PUT    /api/v1/users/me                    # users:write

# FCS Data（實際實作）
GET    /api/v1/fcs/parameters              # fcs:read - 列出所有 PnN/PnS 參數
GET    /api/v1/fcs/events                  # fcs:read - 取得所有 events 資料
POST   /api/v1/fcs/upload                  # fcs:write - 上傳 FCS 檔案
GET    /api/v1/fcs/statistics              # fcs:analyze - 取得統計資料
```

---

### Audit Log API 規格

**GET /api/v1/tokens/{id}/logs**（需 JWT）

```json
{
  "success": true,
  "data": {
    "token_id": "abc123",
    "token_name": "CI/CD Pipeline",
    "total_logs": 150,
    "logs": [
      {
        "timestamp": "2024-01-15T10:30:00Z",
        "ip": "192.168.1.100",
        "method": "GET",
        "endpoint": "/api/v1/fcs/statistics",
        "status_code": 200,
        "authorized": true
      },
      {
        "timestamp": "2024-01-15T10:28:00Z",
        "ip": "192.168.1.100",
        "method": "DELETE",
        "endpoint": "/api/v1/workspaces/5",
        "status_code": 403,
        "authorized": false,
        "reason": "Insufficient permissions"
      }
    ]
  }
}
```

---

### FCS API 詳細規格

使用內建範例 FCS 檔案（34,297 events、26 channels）或允許上傳。

**GET /api/v1/fcs/parameters** (`fcs:read`)

```json
{
  "success": true,
  "data": {
    "total_events": 34297,
    "total_parameters": 26,
    "parameters": [
      { "index": 1, "pnn": "FSC-H", "pns": "FSC-H", "range": 16777215, "display": "LIN" },
      { "index": 2, "pnn": "FSC-A", "pns": "FSC-A", "range": 16777215, "display": "LIN" },
      { "index": 3, "pnn": "SSC-H", "pns": "SSC-H", "range": 16777215, "display": "LIN" },
      { "index": 4, "pnn": "SSC-A", "pns": "SSC-A", "range": 16777215, "display": "LIN" },
      { "index": 5, "pnn": "FL1-H", "pns": "TCRgd FITC-H", "range": 16777215, "display": "LOG" },
      { "index": 6, "pnn": "FL1-A", "pns": "TCRgd FITC-A", "range": 16777215, "display": "LOG" },
      { "index": 7, "pnn": "FL2-H", "pns": "CD4 PE-H", "range": 16777215, "display": "LOG" },
      { "index": 8, "pnn": "FL2-A", "pns": "CD4 PE-A", "range": 16777215, "display": "LOG" },
      { "index": 9, "pnn": "FL3-H", "pns": "CD2 ECD-H", "range": 16777215, "display": "LOG" },
      { "index": 10, "pnn": "FL3-A", "pns": "CD2 ECD-A", "range": 16777215, "display": "LOG" },
      { "index": 11, "pnn": "FL4-H", "pns": "CD56 PC5.5-H", "range": 16777215, "display": "LOG" },
      { "index": 12, "pnn": "FL4-A", "pns": "CD56 PC5.5-A", "range": 16777215, "display": "LOG" },
      { "index": 13, "pnn": "FL5-H", "pns": "CD5 PC7-H", "range": 16777215, "display": "LOG" },
      { "index": 14, "pnn": "FL5-A", "pns": "CD5 PC7-A", "range": 16777215, "display": "LOG" },
      { "index": 15, "pnn": "FL6-H", "pns": "CD34 APC-H", "range": 16777215, "display": "LOG" },
      { "index": 16, "pnn": "FL6-A", "pns": "CD34 APC-A", "range": 16777215, "display": "LOG" },
      { "index": 17, "pnn": "FL7-H", "pns": "CD7 APC-A700-H", "range": 16777215, "display": "LOG" },
      { "index": 18, "pnn": "FL7-A", "pns": "CD7 APC-A700-A", "range": 16777215, "display": "LOG" },
      { "index": 19, "pnn": "FL8-H", "pns": "CD8 APC-A750-H", "range": 16777215, "display": "LOG" },
      { "index": 20, "pnn": "FL8-A", "pns": "CD8 APC-A750-A", "range": 16777215, "display": "LOG" },
      { "index": 21, "pnn": "FL9-H", "pns": "CD3 PB450-H", "range": 16777215, "display": "LOG" },
      { "index": 22, "pnn": "FL9-A", "pns": "CD3 PB450-A", "range": 16777215, "display": "LOG" },
      { "index": 23, "pnn": "FL10-H", "pns": "CD45 KO525-H", "range": 16777215, "display": "LOG" },
      { "index": 24, "pnn": "FL10-A", "pns": "CD45 KO525-A", "range": 16777215, "display": "LOG" },
      { "index": 25, "pnn": "FSC-Width", "pns": "FSC-Width", "range": 10000, "display": "LIN" },
      { "index": 26, "pnn": "Time", "pns": "Time", "range": 900000000, "display": "LIN" }
    ]
  }
}
```

**GET /api/v1/fcs/events** (`fcs:read`)

```json
// GET /api/v1/fcs/events?limit=100&offset=0
{
  "success": true,
  "data": {
    "total_events": 34297,
    "limit": 100,
    "offset": 0,
    "events": [
      {
        "FSC-H": 2500000,
        "FSC-A": 2800000,
        "SSC-H": 1200000,
        "SSC-A": 1350000,
        "FL1-H": 150,
        "FL1-A": 180,
        "FL2-H": 45000,
        "FL2-A": 52000,
        "..."
      }
    ]
  }
}
```

**POST /api/v1/fcs/upload** (`fcs:write`)

```json
{
  "success": true,
  "data": {
    "file_id": "abc123",
    "filename": "sample.fcs",
    "total_events": 34297,
    "total_parameters": 26
  }
}
```

**GET /api/v1/fcs/statistics** (`fcs:analyze`)

```json
{
  "success": true,
  "data": {
    "total_events": 34297,
    "statistics": [
      {
        "parameter": "FSC-A",
        "pns": "FSC-A",
        "display": "LIN",
        "min": 0,
        "max": 16777215,
        "mean": 3250000.5,
        "median": 3100000,
        "std": 1250000.3
      },
      {
        "parameter": "FL2-A",
        "pns": "CD4 PE-A",
        "display": "LOG",
        "min": 0,
        "max": 8500000,
        "mean": 125000.7,
        "median": 45000,
        "std": 280000.2
      },
      {
        "parameter": "FL9-A",
        "pns": "CD3 PB450-A",
        "display": "LOG",
        "min": 0,
        "max": 12000000,
        "mean": 850000.3,
        "median": 620000,
        "std": 750000.8
      }
    ]
  }
}
```

---

### Stub API 回應規格（workspaces、Users）

**成功 (200)**
```json
{
  "success": true,
  "data": {
    "endpoint": "/api/v1/workspaces",
    "method": "GET",
    "required_scope": "workspaces:read",
    "granted_by": "workspaces:admin",
    "your_scopes": ["workspaces:admin", "fcs:read"]
  }
}
```

**權限不足 (403)**
```json
{
  "success": false,
  "error": "Forbidden",
  "data": {
    "required_scope": "workspaces:read",
    "your_scopes": ["fcs:read"]
  }
}
```

**認證失敗 (401)**
```json
{ "success": false, "error": "Unauthorized", "message": "Token expired" }
{ "success": false, "error": "Unauthorized", "message": "Token revoked" }
{ "success": false, "error": "Unauthorized", "message": "Invalid token" }
```

**Rate Limit (429)**
```json
{ "success": false, "error": "Too Many Requests", "data": { "retry_after": 45 } }
```

---

### 技術要求

| 項目 | 要求 |
|------|------|
| 框架 | FastAPI |
| 資料庫 | PostgreSQL |
| 容器化 | Dockerfile + docker-compose.yml |
| 測試 | pytest |

---

## ✅ 必要測試案例（3 個）

### 1. 權限階層繼承驗證

```python
"""
Given: PAT 僅有 workspaces:admin
Then: 可存取 workspaces:read/write/delete ✓
      不可存取 fcs:read ✗（不跨資源）

Given: PAT 僅有 fcs:analyze
Then: 可存取 fcs:read, fcs:write, fcs:analyze ✓
      不可存取 workspaces:read ✗
"""
```

### 2. Token 過期與撤銷處理

```python
"""
Given: 已過期的 PAT → 401 "Token expired"
Given: 已撤銷的 PAT → 401 "Token revoked"
（需區分兩種錯誤訊息）
"""
```

### 3. Token 安全儲存驗證

```python
"""
Given: 建立 PAT 後
Then: DB 無明文、有 prefix、有 hash
      正確 Token → 200
      錯誤 Token（同 prefix）→ 401
"""
```

---

## 📊 評分標準

| 項目 | 權重 |
|------|------|
| 功能完整性 | 30% |
| 程式碼品質 | 25% |
| 安全性 | 20% |
| 測試覆蓋 | 15% |
| 文件與部署 | 10% |

---

## 🎁 加分項目（Optional）

1. Token Regenerate 功能
2. IP 白名單限制
3. CLI 管理工具
4. Redis 快取 Token 驗證結果

---

## ⏰ 時間限制
7天

---

## 📝 提交要求

1. GitHub 公開倉庫
2. `docker-compose up -d` 一鍵啟動（含自動 migration）
3. 內建範例 FCS 檔案（26 channels、34,297 events）
4. README 包含：架構說明、執行方式、API 範例（curl）、設計決策

---

## 💡 參考資源
- [FCS 3.1 Specification](https://www.bioconductor.org/packages/release/bioc/vignettes/flowCore/inst/doc/fcs3.html)
- [FlowIO (Python)](https://github.com/whitews/FlowIO)