# Product Requirements Document (PRD) – ChatTrain MVP 1

## 概要

ローカル Mac 環境と GitHub だけで動作する、チャット型アウトプット・トレーニングプラットフォーム **“ChatTrain”** の最小実用プロトタイプ（MVP 1）を実装する。社員は左ペインの Chat UI で LLM (顧客役など) と対話し、右ペインのドキュメント Preview で業務資料を参照しながら 30 分セッションを完了する。教材は YAML＋資料ファイルのパッケージとして Git で管理・配信する。

## 目標

* **30 分×2 シナリオ** を 5 名のパイロットユーザが完走できる
* LLM から “良い点 / 改善点” を含むフィードバックが受け取れる
* YAML シナリオ／資料を GitHub PR → CI → 本番反映できる
* Retrieval‑only + 正規表現レダクションで機密情報をマスクできる

## 機能要件

### 1. チャット学習セッション

* [ ] 左ペイン：Chat UI（入力欄＋メッセージバブル）
* [ ] 右ペイン：PDF / Markdown Preview、Split‑Pane で幅可変
* [ ] LLM からの更問い＆3 秒 typing indicator
* [ ] セッション完了後にフィードバック画面を表示・エクスポート

### 2. 教材パッケージ管理

* [ ] `content/{domain}/{scenario}/{version}/` に YAML + 資料格納
* [ ] YAML スキーマ lint & mock‑run を CI で自動検証
* [ ] Git タグ (SemVer) を本番バージョンとして pin

### 3. Orchestrator & 評価エンジン

* [ ] FastAPI で WebSocket `/chat/stream` を提供
* [ ] LangChain RAG：pgvector から k=3 スニペット取得 → 100 token 要約
* [ ] ルールベース (must\_include) + GPT Judge でフィードバック生成
* [ ] セッション／メッセージ／フィードバックを SQLite に保存

### 4. セキュリティ & マスキング

* [ ] Retrieval‑only 方式をデフォルトとし、外部 LLM へ全文送信禁止
* [ ] 固有表現（顧客名・口座番号）の正規表現レダクション
* [ ] `.env` に API Key、Git にはコミットしない

### 5. CI / QA

* [ ] GitHub Actions：`yamllint` → schema‑check → pytest（mock LLM）
* [ ] コンテンツ PR は CODEOWNERS 承認必須
* [ ] `variant: A|B` 付き YAML で A/B テストを自動割当て

## 成功基準

* 5 名 × 2 シナリオの完了率 100 %
* 各セッションで “改善点” が 1 件以上フィードバックされる
* CI パイプラインを経ずに main へマージされた PR が 0 件
* 機密文字列が LLM プロンプトに含まれないことをユニットテストで確認

## 技術スタック

* **フロント**: React + Vite + Radix UI + Tailwind
* **バックエンド**: FastAPI + LangChain + Celery
* **データベース**: SQLite (dev) / PostgreSQL + pgvector (Docker)
* **LLM**: OpenAI / Azure OpenAI (gpt‑4o)
* **CI/CD**: GitHub Actions
* **環境構築**: Docker Compose、Makefile

---

最終更新: 2025‑06‑15



以下参考

# ChatTrain MVP1 プロジェクトドキュメント

## 1. プロジェクト概要

* **目的**: 社員が業務シチュエーションを模したチャットを通じ、アウトプット駆動でQCDを向上させるトレーニング環境（MVP1）を、クラウドを用いず **Mac ローカル実行 + GitHub** で構築する。
* **対象ユーザ**: 研修パイロット 5 名（CS 新任社員想定）。
* **成功基準**: 30 分セッション×2 シナリオを各自完了し、フィードバックコメントを受け取れる。

## 2. MVP1 スコープ

| # | 項目           | 内容                                                               |
| - | ------------ | ---------------------------------------------------------------- |
| 1 | チャット UI      | ブラウザ ([http://localhost](http://localhost)) で動作。React + Vite。    |
| 2 | Orchestrator | FastAPI + LangChain。YAML シナリオ読込・LLM 呼出・ループ制御。                    |
| 3 | 教材管理         | GitHub repo 直下 `content/` フォルダに YAML/PDF/MD を配置。バージョン管理は Git タグ。 |
| 4 | Vector 検索    | PostgreSQL + pgvector (Docker)。                                  |
| 5 | LLM          | 外部 API (Azure OpenAI / OpenAI) 使用可。API Key は `.env` に保存。         |
| 6 | マスキング        | Retrieval-only 方式 (100 token 要約) + 固有表現の簡易 redaction。            |
| 7 | CI           | GitHub Actions で lint / unit / e2e / schema-check。               |
| 8 | 評価/フィードバック   | ルールベース + GPT Judge (良かった点 / 改善点)。数値スコア化なし。                       |
| 9 | ログ           | SQLite (dev) / Postgres (prod) に学習ログ保存。非アクティブ化後 2 年で自動削除。        |

## 3. 成果物一覧

* `README.md`: 起動手順・依存ツール。
* `docker-compose.yml`: pgvector, FastAPI サービス起動。
* `src/frontend/`: React UI。
* `src/backend/`: FastAPI アプリケーション。
* `content/`: シナリオパッケージ (YAML + 資料)。
* `.github/workflows/ci.yml`: CI パイプライン。

## 4. 役割と責任

| 役割            | 担当         | 主な責務            |
| ------------- | ---------- | --------------- |
| Product Owner | (あなた)      | 要件確定、受入確認。      |
| Trainer       | T.Trainer  | シナリオ作成、PR 提出。   |
| Reviewer      | R.Reviewer | シナリオレビュー、QA。    |
| Dev Lead      | D.Dev      | インフラ・CI セットアップ。 |

## 5. ローカル開発環境

1. **必須ツール**

   * macOS 12+
   * Docker Desktop
   * Node 20+
   * Python 3.11 (pyenv 推奨)
2. **セットアップ**

   ```bash
   git clone git@github.com:your-org/chattrain.git
   cd chattrain
   make setup   # venv, pre‑commit, npm install
   make dev     # docker compose up + Vite dev
   ```

## 6. リポジトリ構成

```
chattrain/
 ├─ src/
 │   ├─ frontend/
 │   └─ backend/
 ├─ content/
 │   └─ onboarding/claim_handling/v1/
 ├─ tests/
 ├─ .github/workflows/
 └─ docs/
```

## 7. YAML シナリオ スキーマ（抜粋）

```yaml
id: string              # 必須、一意
version: semver         # 必須
smart_goals:            # 必須 (≥1)
  - S: string
    M: string
    A: string
    R: string
    T: string
llm_profile:
  model: string
  temperature: float (0‑1)
steps:                  # Array
  - role: bot|user|feedback
    msg: string
    attachments?: [file]
    expected?: string   # user ステップ時
    rubric?:            # 評価基準
      must_include?: [string]
      nice_to_have?: [string]
complete_conditions?:   # 例: loop_until, step 到達
```

## 8. アプリ詳細

### 8.1 フロントエンド

* React + Radix UI + Tailwind。
* **レイアウト**: 左ペインに Chat UI、右ペインにドキュメント Preview ビューア（PDF/Markdown）を固定表示し、リサイズ可能な Split Pane とする。
* 状態管理: Zustand。
* PDF/MD ビューア内蔵。

### 8.2 バックエンド

* FastAPI ルータ構成:

  * `/chat/stream` (WebSocket)
  * `/scenario/{id}`
  * `/export/{session_id}`
* Celery + Redis (optional) で非同期 GPT Judge。

### 8.3 Vector DB

* docker‑compose で `postgres:16` + `pgvector` 拡張。

## 9. セキュリティとマスキング

* Retrieval‑only: Vector 結果 (k=3) → 100 token Summarizer。
* Regex Redaction: `/[A-Z]{2}\d{6}|\d{4}-\d{4}-\d{4}-\d{4}/` → `{{REDACTED}}`。
* `.env` に `OPENAI_API_KEY`. `.gitignore` 済み。

## 10. CI / QA

```yaml
name: CI
on: [push, pull_request]
jobs:
  build:
    runs-on: macos-14
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.11'}
      - run: pip install -r requirements.txt
      - run: pytest
      - run: yamllint content/**/*.yaml
```

* Dry‑run シナリオ: `pytest -m scenario` がモック LLM で 1 往復シミュ。

## 11. テスト戦略

| 層     | ツール                 | 目的               |
| ----- | ------------------- | ---------------- |
| フロント  | Vitest + Playwright | UI コンポーネント / E2E |
| バック   | Pytest              | API, Judge Logic |
| コンテンツ | Schema + Dry‑run    | YAML 構文 & 品質     |

## 12. データ＆監査ログ

* SQLite に `sessions`, `messages`, `feedback`。
* `cron`(Celery beat) で 30 日毎、非アクティブユーザ→2 年で purge。

## 13. ロードマップ

| 週 | マイルストーン                           |
| - | --------------------------------- |
| 1 | リポジトリ初期化・環境構築完了                   |
| 2 | YAML スキーマ確定・サンプル 2 本              |
| 3 | Orchestrator → Front WebSocket 通信 |
| 4 | Vector 検索+マスキング PoC 完了            |
| 5 | GPT Judge 組込・Feedback UI          |
| 6 | QA & 改善 → パイロット開始                 |

## 14. リスクと対策

| リスク              | 影響       | 対策                           |
| ---------------- | -------- | ---------------------------- |
| LLM API コスト増     | 予算オーバ    | トークンログ計測 & rate‑limit        |
| Redaction 漏れ     | 情報漏えい    | 2 段階正規表現 + manual review     |
| Vector DB スキーマ崩壊 | RAG 精度低下 | Migration test + version pin |

## 15. 用語集

* **Orchestrator**: LLM、RAG、評価を統括するバックエンド。
* **RAG**: Retrieval‑Augmented Generation。
* **SMART**: Specific, Measurable, Achievable, Relevant, Time‑bound。

---

最終更新: 2025‑06‑14
