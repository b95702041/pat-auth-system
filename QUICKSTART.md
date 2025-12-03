# 快速入門指南

## 🚀 5 分鐘快速啟動

### 1. 啟動服務

```bash
# 確保在專案根目錄
cd pat-auth-system

# 一鍵啟動（Docker 會自動執行 migration）
docker-compose up -d

# 查看日誌確認啟動成功
docker-compose logs -f api
# 看到 "Application startup complete" 即表示成功
```

### 2. 驗證服務

訪問 API 文件：http://localhost:8000/docs

### 3. 快速測試

```bash
# 執行示例腳本（需要安裝 jq）
./examples.sh

# 或者手動測試
# 1. 註冊使用者
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "email": "test@example.com", "password": "password123"}'

# 2. 登入
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```

## 📝 開發工作流

### 使用 Makefile（推薦）

```bash
make help       # 查看所有可用命令
make up         # 啟動服務
make logs       # 查看日誌
make test       # 執行測試
make shell      # 進入容器
make down       # 停止服務
```

### 資料庫管理

```bash
# 執行 migration
docker-compose exec api alembic upgrade head

# 檢查當前版本
docker-compose exec api alembic current

# 創建新的 migration
docker-compose exec api alembic revision --autogenerate -m "description"
```

## 🧪 執行測試

```bash
# 執行所有測試
docker-compose exec api pytest tests/ -v

# 執行特定測試
docker-compose exec api pytest tests/test_permissions.py::test_permission_hierarchy_inheritance -v

# 查看測試覆蓋率
docker-compose exec api pytest tests/ --cov=app --cov-report=html
# 覆蓋率報告在 htmlcov/index.html
```

## 🔍 常用 API 流程

### 完整流程示例

```bash
# Step 1: 註冊並登入
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "email": "demo@example.com", "password": "pass123"}'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "pass123"}' \
  | jq -r '.data.access_token' > jwt.txt

# Step 2: 創建 PAT
curl -X POST http://localhost:8000/api/v1/tokens \
  -H "Authorization: Bearer $(cat jwt.txt)" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Token", "scopes": ["fcs:analyze"], "expires_in_days": 90}' \
  | jq -r '.data.token' > pat.txt

# Step 3: 使用 PAT 存取資源
curl -X GET http://localhost:8000/api/v1/fcs/parameters \
  -H "Authorization: Bearer $(cat pat.txt)"

curl -X GET http://localhost:8000/api/v1/fcs/statistics \
  -H "Authorization: Bearer $(cat pat.txt)"
```

## 🐛 疑難排解

### 服務無法啟動

```bash
# 檢查容器狀態
docker-compose ps

# 重啟服務
docker-compose restart

# 完全重建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 資料庫問題

```bash
# 進入資料庫容器
docker-compose exec db psql -U pat_user -d pat_db

# 檢查資料表
\dt

# 退出
\q
```

### 查看詳細日誌

```bash
# API 日誌
docker-compose logs -f api

# 資料庫日誌
docker-compose logs -f db

# 所有服務
docker-compose logs -f
```

## 📊 權限測試案例

### 測試階層式權限

```bash
# 創建具有 workspaces:admin 的 Token
# 應該可以存取 read, write, delete
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/tokens \
  -H "Authorization: Bearer $(cat jwt.txt)" \
  -H "Content-Type: application/json" \
  -d '{"name": "Admin", "scopes": ["workspaces:admin"], "expires_in_days": 30}' \
  | jq -r '.data.token')

# 測試 read（應該成功）
curl -X GET http://localhost:8000/api/v1/workspaces \
  -H "Authorization: Bearer $TOKEN"

# 測試 write（應該成功）
curl -X POST http://localhost:8000/api/v1/workspaces \
  -H "Authorization: Bearer $TOKEN"

# 測試跨資源（應該失敗）
curl -X GET http://localhost:8000/api/v1/fcs/parameters \
  -H "Authorization: Bearer $TOKEN"
```

## 🎓 學習資源

- **API 文件**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **完整 README**: 查看 README.md
- **測試範例**: 查看 tests/test_permissions.py
- **API 範例**: 執行 ./examples.sh

## 🔄 開發流程

1. **修改程式碼**：直接修改 `app/` 目錄下的文件
2. **自動重載**：uvicorn 會自動檢測變更並重載
3. **測試**：`make test` 執行測試
4. **檢查日誌**：`make logs` 查看運行日誌

## 📦 部署到生產環境

### 環境變數設定

複製 `.env.example` 為 `.env` 並修改：

```bash
# 必須修改
SECRET_KEY=<使用強隨機字串>
DATABASE_URL=<生產環境資料庫 URL>

# 建議修改
ACCESS_TOKEN_EXPIRE_MINUTES=15
RATE_LIMIT_PER_MINUTE=30
```

### Docker Compose 生產配置

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  api:
    restart: always
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
    # 移除 --reload 選項
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

**需要幫助？** 查看完整 README.md 或提交 Issue
