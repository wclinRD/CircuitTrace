# CircuitTrace

CircuitTrace 是一款專為 macOS 打造的高效能 Verilog 追蹤與檢視工具，介面與操作邏輯致敬工業界標準 EDA 工具（如 Synopsys Verdi）。透過現代化的 Web 前端技術與強大的 Python 分析後端，為硬體工程師帶來極致流暢的 Trace 體驗。

## ✨ 核心特色 (Features)

*   **專為 macOS 打造**：打包為獨立的 `.app` 應用程式，雙擊即可開啟，免去繁雜的環境設定。
*   **高速程式碼編輯器**：內建 Monaco Editor，提供流暢的 Verilog 語法高亮、全域快捷鍵與多頁籤切換支援。
*   **樹狀追蹤面板 (OneTrace)**：
    *   **Trace Driver / Trace Load / Trace Connection**：一鍵追蹤訊號來源與去向。
    *   **階層式 Tree-Table**：追蹤結果以清晰的樹狀表格呈現。
    *   **智慧跳轉**：點擊追蹤結果，編輯器會自動跳轉至對應的檔案與行數。
    *   **快捷鍵支援**：支援 `Alt+Shift+D` / `L` / `C` 快速觸發 Trace。
    *   **右鍵管理**：支援在追蹤群組上點擊右鍵以清除部分或所有歷史紀錄。
*   **模組階層檢視 (Module Hierarchy)**：一目瞭然地檢視專案中所有的 Module 依賴關係，並點擊展開對應的檔案。
*   **高自由度的 UI 佈局**：支援水平與垂直滑鼠拖曳（Resizer），自訂最適合您的視窗大小。

## 🛠️ 技術棧 (Tech Stack)

*   **Frontend**: React 19, Vite, Monaco Editor, Lucide React (Icons)
*   **Backend**: Python 3.11, pywebview (Native UI Bridge), Pyverilog (AST / Dataflow 解析)
*   **Bundler**: PyInstaller (macOS App 打包)

## 🚀 如何編譯與執行 (Build & Run)

### 需求環境
*   `Node.js` & `npm`
*   `uv` (Python 套件管理器)

### 一鍵打包 (Build Release)

專案內附有自動化編譯腳本，會自動編譯前端、後端並透過 PyInstaller 打包為 macOS 專屬的 `CircuitTrace.app`：

```bash
chmod +x build_release.sh
./build_release.sh
```

編譯完成後，您可以在 `release/` 資料夾下找到 `CircuitTrace.app`，雙擊即可執行。

### 開發模式 (Development)

若您想修改程式碼並即時預覽：

1. **啟動前端 Dev Server**：
    ```bash
    cd frontend
    npm install
    npm run dev
    ```
2. **啟動後端** (並指定開發模式載入 local URL)：
    ```bash
    cd backend
    uv sync
    # (後端需要修改 desktop_app.py 暫時讀取 localhost:5173 進行除錯)
    uv run src/desktop_app.py
    ```

## 📂 專案結構

```text
CircuitTrace/
├── frontend/           # React + Vite 前端介面
│   ├── src/App.jsx     # 核心 UI 邏輯與 Monaco 整合
│   └── src/App.css     # 核心樣式與 Flex 佈局
├── backend/            # Python 後端邏輯
│   ├── src/api.py      # 提供給前端的 API
│   ├── src/tracer.py   # Pyverilog 追蹤與解析邏輯
│   └── src/desktop_app.py # pywebview 視窗建立入口
├── build_release.sh    # macOS App 自動打包腳本
└── CircuitTrace.icns   # 專屬 App 圖示
```

## 📝 授權 (License)

MIT License
