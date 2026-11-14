# 印章行事曆

印章簿、行事曆、列表和許願池。網頁 app，可加入 iPhone 主畫面。

- `index.html`：頁面原始碼（所有功能）
- `standalone/`：獨立版外殼（Google 登入、Firestore、主畫面設定）與建置腳本
- `docs/`：建置結果，由 GitHub Pages 發布

改完 `index.html` 或 `standalone/` 後重新建置：

```bash
python3 standalone/build.py
```
