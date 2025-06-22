# ChatTrain MVP1 並列開発タスク定義 (Simplified)

## 概要

簡素化されたMVP1設計に基づく並列開発タスクです。SQLite + 4 API + 固定UI + 基本機能に焦点を当て、5名のパイロットユーザーが2シナリオを完走できる最小実装を目指します。

## 並列開発の原則

### ✅ 簡素化による利点
1. **最小依存**: SQLite単一ファイル、API 4つのみ
2. **独立実装**: 各タスクが他を必要としない
3. **高速統合**: シンプルなインターフェース
4. **迅速検証**: 最小機能での動作確認

### 🎯 MVP1成功基準
- 5名 × 2シナリオ = 10セッションの完走
- LLMフィードバック機能
- GitHub管理のYAMLシナリオ
- 基本的なデータマスキング

## タスク1: Backend Core (SQLite + FastAPI)

### 👤 担当範囲
- SQLite データベース設計・初期化
- FastAPI アプリケーション + 4エンドポイント
- WebSocket チャット機能
- 基本的なエラーハンドリング

### 📁 実装ファイル
```
src/backend/
├── app/
│   ├── main.py              # FastAPI アプリ
│   ├── database.py          # SQLite 操作
│   ├── models.py            # Pydantic モデル
│   └── websocket.py         # WebSocket ハンドラー
├── requirements.txt         # 最小依存関係
└── Dockerfile              # シンプルコンテナ
```

### 🔌 モックサービス
```python
# Mock services for independent development
class MockLLMService:
    async def generate_response(self, messages, config):
        return {"content": "Mock LLM response", "tokens": 50}

class MockMaskingService:
    def mask_content(self, text):
        return text  # No masking during development
```

### ✅ 完了条件
- [ ] SQLite + 3テーブル作成
- [ ] GET /api/scenarios (mock data)
- [ ] POST /api/sessions 
- [ ] GET /api/documents/{scenario_id}/{filename}
- [ ] GET /api/health
- [ ] WebSocket /chat/{session_id}
- [ ] FastAPI サーバー起動確認

---

## タスク2: Frontend UI (React Fixed Layout)

### 👤 担当範囲
- React + TypeScript セットアップ
- 固定レイアウト チャットUI
- WebSocket クライアント
- 基本的なドキュメント表示

### 📁 実装ファイル
```
src/frontend/
├── src/
│   ├── App.tsx              # メインアプリ
│   ├── components/
│   │   ├── ChatInterface.tsx # チャット画面
│   │   ├── MessageList.tsx   # メッセージ表示
│   │   ├── MessageInput.tsx  # 入力フォーム
│   │   └── DocumentViewer.tsx # 文書表示
│   ├── hooks/
│   │   └── useWebSocket.ts   # WebSocket フック
│   └── services/
│       └── api.ts            # API クライアント
├── package.json
└── vite.config.ts
```

### 🔌 モックAPI
```typescript
// Mock backend for independent development
export const mockAPI = {
  getScenarios: () => Promise.resolve({
    scenarios: [
      { id: "claim_handling_v1", title: "Insurance Claims", documents: ["guide.pdf"] }
    ]
  }),
  createSession: () => Promise.resolve({ session_id: "mock-session-123" })
};

// Mock WebSocket
export class MockWebSocket {
  send(data: string) {
    console.log("Mock WS send:", data);
    setTimeout(() => this.onmessage?.({ data: '{"type":"assistant_message","content":"Mock response"}' }), 1000);
  }
}
```

### ✅ 完了条件
- [ ] Vite + React + TypeScript セットアップ
- [ ] 固定2ペインレイアウト（60%チャット + 40%ドキュメント）
- [ ] WebSocket接続・メッセージ送受信
- [ ] PDF/Markdown表示機能
- [ ] シナリオ選択画面
- [ ] http://localhost:3000 で動作確認

---

## タスク3: LLM Integration (OpenAI Direct)

### 👤 担当範囲
- OpenAI SDK統合
- シンプルなプロンプト生成
- 基本的な評価・フィードバック
- トークン使用量追跡

### 📁 実装ファイル
```
src/backend/app/services/
├── llm_service.py           # OpenAI 統合
├── feedback_service.py      # 簡単な評価
└── prompt_builder.py        # プロンプト構築
```

### 🔌 モックインターフェース
```python
# Mock for database and scenarios
class MockScenarioService:
    def get_scenario(self, scenario_id):
        return {
            "bot_messages": [{"content": "Mock bot message", "expected_keywords": ["help"]}],
            "llm_config": {"model": "gpt-4o-mini", "temperature": 0.7}
        }

class MockDatabaseService:
    async def save_message(self, session_id, role, content):
        return "mock-message-id"
```

### ✅ 完了条件
- [ ] OpenAI SDK設定・接続確認
- [ ] シンプルなチャット応答生成
- [ ] キーワードベース評価機能
- [ ] フィードバック生成（良い点・改善点）
- [ ] 基本的なトークン制限（200トークン/応答）
- [ ] エラーハンドリング（API制限など）

---

## タスク4: Content Management (YAML + Samples)

### 👤 担当範囲
- 簡素化YAMLスキーマ実装
- サンプルシナリオ2個作成
- YAMLローダー・バリデーター
- ファイルサーバー機能

### 📁 実装ファイル
```
src/backend/app/content/
├── loader.py                # YAML ローダー
├── validator.py             # スキーマ検証
└── file_server.py           # ドキュメント配信

content/
├── claim_handling_v1/
│   ├── scenario.yaml
│   ├── claim_guide.pdf
│   └── examples.md
└── customer_service_v1/
    ├── scenario.yaml
    ├── service_manual.pdf
    └── scripts.md

scripts/
└── validate_scenarios.py    # 検証スクリプト
```

### 🔌 モックインターフェース
```python
# Mock for database integration
class MockDatabaseService:
    def cache_scenario(self, scenario_data):
        print(f"Mock: Caching scenario {scenario_data['id']}")
```

### ✅ 完了条件
- [ ] 簡素化YAMLスキーマ実装
- [ ] 2つのサンプルシナリオ作成
- [ ] YAML読み込み・検証機能
- [ ] PDF/Markdownファイル配信
- [ ] バリデーションスクリプト
- [ ] content/ ディレクトリ構造作成

---

## タスク5: Security (Basic Masking)

### 👤 担当範囲
- 基本的な正規表現マスキング
- シンプルな入力検証
- 基本的なレート制限
- セキュリティテスト

### 📁 実装ファイル
```
src/backend/app/security/
├── masking.py               # データマスキング
├── validator.py             # 入力検証
└── rate_limiter.py          # レート制限

tests/security/
├── test_masking.py          # マスキングテスト
└── test_validation.py       # 検証テスト
```

### 🔌 モックインターフェース
```python
# Mock for testing
class MockUserInput:
    sensitive_data = [
        "My account AC-123456 and card 1234-5678-9012-3456",
        "Email john@example.com phone 555-123-4567",
        "Policy P-789456 customer ID C-654321"
    ]
```

### ✅ 完了条件
- [ ] 基本正規表現パターン実装（口座番号、カード番号、メール）
- [ ] シンプルな入力長制限・文字制限
- [ ] メモリベースレート制限（20req/min）
- [ ] マスキング有効性テスト
- [ ] セキュリティ検証スクリプト

---

## タスク6: Testing (Essential Coverage)

### 👤 担当範囲
- 基本的なAPIテスト
- データベーステスト
- マスキングテスト
- 手動テスト手順書

### 📁 実装ファイル
```
tests/
├── test_api.py              # API テスト
├── test_database.py         # DB テスト  
├── test_websocket.py        # WebSocket テスト
├── test_integration.py      # 統合テスト
└── conftest.py              # pytest 設定

scripts/
├── integration_test.py      # 統合テストスクリプト
└── manual_test_guide.md     # 手動テスト手順
```

### ✅ 完了条件
- [ ] 4つのAPIエンドポイントテスト
- [ ] SQLite操作テスト
- [ ] WebSocket通信テスト
- [ ] データマスキングテスト
- [ ] 統合テストスクリプト
- [ ] 手動テスト手順書

---

## タスク7: Deployment (Simple Setup)

### 👤 担当範囲
- 開発環境セットアップスクリプト
- 簡単なDockerfile
- 環境設定管理
- READMEとドキュメント

### 📁 実装ファイル
```
├── docker-compose.yml       # 開発環境
├── Dockerfile.backend       # バックエンドコンテナ
├── Dockerfile.frontend      # フロントエンドコンテナ
├── scripts/
│   ├── setup.sh             # 環境セットアップ
│   └── start_dev.sh         # 開発サーバー起動
├── .env.example             # 環境変数テンプレート
├── README.md                # セットアップガイド
└── Makefile                 # 便利コマンド
```

### ✅ 完了条件
- [ ] 開発環境セットアップスクリプト
- [ ] Docker設定（SQLiteボリューム）
- [ ] 環境変数管理
- [ ] README.md作成
- [ ] make dev コマンド
- [ ] パイロットユーザー向けガイド

## 🔄 統合フェーズ

### Week 1: Core Foundation
- **Day 1-2**: Backend SQLite + API
- **Day 3-4**: Frontend React UI
- **Day 5**: 基本統合確認

### Week 2: Features Integration  
- **Day 1-2**: LLM統合 + Content管理
- **Day 3-4**: Security + Testing
- **Day 5**: 全機能統合確認

### Week 3: Final Integration
- **Day 1-2**: Deployment + 最終テスト
- **Day 3-4**: パイロットユーザー準備
- **Day 5**: MVP1リリース

## 📊 進捗管理

### 完了チェックリスト
- [ ] **Task 1**: Backend Core完了
- [ ] **Task 2**: Frontend UI完了
- [ ] **Task 3**: LLM Integration完了
- [ ] **Task 4**: Content Management完了
- [ ] **Task 5**: Security完了
- [ ] **Task 6**: Testing完了
- [ ] **Task 7**: Deployment完了
- [ ] **Integration**: 全体統合完了
- [ ] **Validation**: パイロットテスト準備完了

### 依存関係マップ
```
Backend Core ──┐
               ├─→ Integration Test
Frontend UI ───┤
               └─→ Manual Testing
LLM Integration ─┐
                 ├─→ End-to-End Testing
Content Mgmt ────┤
                 └─→ Pilot User Test
Security ────────┘

Testing ─────────→ Deployment ─────────→ Release
```

---

この簡素化された並列開発計画により、MVP1の実装時間を大幅に短縮し、5名のパイロットユーザーが2シナリオを確実に完走できるシステムを構築します。