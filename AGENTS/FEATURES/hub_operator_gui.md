# Feature: Hub Operator GUI (Streamlit)

## Status
[Active - Implemented]

**Implemented:**
- ✅ `gui/app.py` — entry point, ~35 dòng
- ✅ `gui/session.py` — session state, local file persistence, mask_secret
- ✅ `gui/tab_invite.py` — Tab 1: tạo trạm tự động (Admin PAT + deploy key + snapshot workflow)
- ✅ `gui/tab_config.py` — Tab 2: Cấu hình tải dữ liệu (lưu Admin PAT)
- ✅ `gui/tab_health.py` — Tab 3: Health
- ✅ `github_api.py` — tạo repo, sinh SSH key pair, gắn deploy key, cài workflow release snapshot

**Cần hoàn thiện:**
- 🚧 Test E2E với bot account thật
- 🚧 Cập nhật tests Edge cho SSH flow

---

## Mở GUI

```bash
# Double-click:
scripts/run-hub-gui-dev.bat

# Hoặc terminal:
cd hub
uv run carevl-hub gui
# → http://127.0.0.1:8501
```

---

## Cấu trúc module

```
hub/carevl_hub/
├── github_api.py       ← tạo repo, sinh SSH key, gắn deploy key
├── admin.py            ← encode_invite_code() (hỗ trợ ssh_private_key / PAT legacy)
└── gui/
    ├── app.py          ← entry point, main() + tabs
    ├── session.py      ← session state, local file, mask_secret
    ├── tab_invite.py   ← Tab 1: tạo trạm tự động
    ├── tab_config.py   ← Tab 2: cấu hình (Admin PAT lưu ở đây)
    └── tab_health.py   ← Tab 3: health check
```

---

## Các tab

| Tab | File | Mục đích | Dùng khi nào |
|-----|------|----------|--------------|
| **🎫 Tạo mã kích hoạt** | `tab_invite.py` | Tạo repo + deploy key + invite code | **DÙNG ĐẦU TIÊN** |
| **📊 Cấu hình tải dữ liệu** | `tab_config.py` | Lưu Admin PAT, org, encryption key | Lần đầu setup + khi tải dữ liệu |
| **🏥 Health** | `tab_health.py` | Version, CWD, session info | Debug |

---

## Quy trình sử dụng

### Lần đầu tiên (setup 1 lần)

1. Tạo **Classic PAT** trên GitHub: https://github.com/settings/tokens
   - Chọn **"Generate new token (classic)"**
   - Scope: **`repo`**
2. Mở Hub GUI → Tab **"📊 Cấu hình tải dữ liệu"**
3. Điền PAT → bấm **"💾 Lưu file"** (để không phải nhập lại)

### Mỗi lần tạo trạm mới (< 1 phút)

1. Tab **"🎫 Tạo mã kích hoạt"**
2. Thấy `✅ Dùng PAT của: <username>` → điền form:
   - **Station ID**: `TRAM_001`
   - **Tên trạm**: `Trạm Y Tế Xã A`
   - **Encryption Key**: tùy chọn
3. Bấm **"🚀 Tạo trạm"** → tự động:
   - Tạo private repo
   - Sinh SSH deploy key
   - Push workflow `.github/workflows/release-snapshot.yml`
   - Generate invite code
4. Copy mã → gửi Zalo/Email cho trạm

### Trạm Edge nhận mã

Trạm tự làm: mở Edge app → `/provision/` → dán mã → New/Restore → PIN → xong.

---

## FAQ

**Q: Lần đầu mở GUI làm gì?**
→ Tab Cấu hình → điền Classic PAT → lưu file → sang Tab Tạo mã

**Q: Classic PAT tạo ở đâu?**
→ https://github.com/settings/tokens → "Generate new token (classic)" → scope `repo`

**Q: 10 trạm phải tạo 10 lần?**
→ PAT nhập 1 lần, mỗi trạm: điền form → bấm nút → xong (< 1 phút/trạm)

**Q: Deploy key khác PAT thế nào?**
→ Deploy key chỉ có quyền trên 1 repo cụ thể, an toàn hơn PAT. Trạm dùng deploy key để clone/push; GitHub Actions trong repo dùng `GITHUB_TOKEN` để tạo Release, nên không cần nhét PAT vào invite code.

**Q: Encryption key lấy ở đâu (Tab 2)?**
→ Chính là key đã điền ở Tab 1 khi tạo invite code. Phải trùng y chang.

---

## Related Documents

- [30. Hub Auto-Provisioning: Admin PAT + Deploy Key](../ACTIVE/30_Hub_Auto_Provisioning.md)
- [31. Snapshot Upload via GitHub Actions](../ACTIVE/31_Snapshot_Upload_Via_GitHub_Actions.md)
- [17. Invite Code Authentication](../ACTIVE/17_Invite_Code_Authentication.md)
- [29. Hub Operator GUI (Streamlit)](../ACTIVE/29_Hub_Operator_Gui_Streamlit.md)
- [08. Hướng dẫn Admin](../ACTIVE/08_Huong_Dan_Admin.md)
