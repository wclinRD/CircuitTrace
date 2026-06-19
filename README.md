# CircuitTrace

CircuitTrace 是一款專為 macOS 打造的高效能 Verilog 追蹤與檢視工具，介面與操作邏輯致敬工業界標準 EDA 工具（如 Synopsys Verdi）。透過現代化的 Web 前端技術與強大的 Python 分析後端，為硬體工程師帶來極致流暢的 Trace 體驗。

## ✨ 核心特色 (Features)

*   **專為 macOS 打造**：打包為獨立的 `.app` 應用程式，雙擊即可開啟，免去繁雜的環境設定。
*   **高速程式碼編輯器**：內建 Monaco Editor，提供流暢的 Verilog 語法高亮、全域快捷鍵與多頁籤切換支援。
*   **樹狀追蹤面板 (OneTrace)**：
    *   **Trace Driver / Trace Load / Trace Connection**：一鍵追蹤訊號來源與去向。
    *   **精準 AST 定位**：透過 `pyslang` 強大的 `lookupName` 支援完整層級路徑精準解析（如 `tb.u_soc.u_cpu.clk`）。
    *   **階層式 Tree-Table**：追蹤結果以清晰的樹狀表格呈現。
    *   **智慧跳轉**：點擊追蹤結果，編輯器會自動跳轉至對應的檔案與行數。
    *   **快捷鍵支援**：支援 `Alt+Shift+D` / `L` / `C` 快速觸發 Trace。
    *   **右鍵管理**：支援在追蹤群組上點擊右鍵以清除部分或所有歷史紀錄。
*   **波形檢視與互動 (Surfer Wasm Engine)**：
    *   內建高效能的 Rust/WebAssembly 波形檢視器 (Surfer)。
    *   支援在程式碼與波形之間 **雙向互動 (Cross-Probing)**：包含從程式碼 `Ctrl+W` 快速將信號加入波形，以及從波形視窗雙擊信號反查原始碼 Driver。
    *   **獨立彈出視窗 (Pop-out Window)**：支援將波形獨立為多視窗檢視，並智慧繼承主視窗中已選取的觀察信號。
*   **模組階層檢視 (Module Hierarchy)**：一目瞭然地檢視專案中所有的 Module 依賴關係，並點擊展開對應的檔案。
*   **高自由度的 UI 佈局**：支援水平與垂直滑鼠拖曳（Resizer），自訂最適合您的視窗大小。

## 🛠️ 技術棧 (Tech Stack)

*   **Frontend**: React 19, Vite, Monaco Editor, Lucide React (Icons)
*   **Backend**: Python 3.11, FastAPI, pywebview (Native UI Bridge)
*   **EDA Engine**: `pyslang` (High-performance SystemVerilog AST / Dataflow Parsing)
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
│   ├── src/tracer.py   # pyslang AST 追蹤與解析邏輯
│   └── src/desktop_app.py # pywebview 視窗建立入口
├── build_release.sh    # macOS App 自動打包腳本
└── CircuitTrace.icns   # 專屬 App 圖示
```

## 📝 授權 (License)

MIT License
