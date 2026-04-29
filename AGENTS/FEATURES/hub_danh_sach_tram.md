# Feature: Hub - Danh sách trạm (Station Registry)

## Status
[Active - Implemented]

- DB schema: xong
- Backend: xong
- UI: xong ✅ (dùng st.dataframe)

## Context

Hub Admin hiện tại không có bảng tập trung để xem danh sách các trạm đã tạo. Mỗi lần tạo trạm chỉ xuất file `.txt` riêng, không thể:

- Query "trạm nào active"
- Copy lại mã kích hoạt cũ (khi trạm hỏng máy, cần restore)
- Revoke trạm từ giao diện (phải vào GitHub xóa deploy key thủ công)
- Thống kê "tháng này tạo mấy trạm"

## Decision

Tạo Tab mới "📋 Danh sách trạm" trên Hub GUI (Streamlit), kèm SQLite local để lưu trữ.

### Database schema

```sql
CREATE TABLE stations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id TEXT UNIQUE NOT NULL,
    station_name TEXT NOT NULL,
    repo_url TEXT NOT NULL,
    invite_code TEXT NOT NULL,        -- để Admin copy lại khi cần
    encryption_key TEXT,              -- NULL nếu không dùng mã hóa
    deploy_key_id TEXT NOT NULL,      -- GitHub deploy key ID (để revoke)
    admin_pat TEXT NOT NULL,          -- PAT của Hub Admin (để tạo trạm khác, revoke)
    created_at TEXT NOT NULL,         -- ISO 8601
    status TEXT DEFAULT 'active',     -- 'active' | 'revoked'
    last_sync_at TEXT,                -- ISO 8601 (lần cuối Hub pull)
    sync_count INTEGER DEFAULT 0,    -- số lần Hub pull thành công
    notes TEXT                        -- optional, ghi chú admin
);
```

**Lưu ý:** `admin_pat` cần được lấy từ Tab Cấu hình trước khi tạo trạm, và có thể hiển thị trong UI (masked) để Admin biết đang dùng PAT nào.

### Giao diện (Streamlit)

```
┌─────────────────────────────────────────────────────────────────────┐
│  📋 Danh sách trạm                              [+ Tạo trạm mới]    │
├─────────────────────────────────────────────────────────────────────┤
│  Tìm kiếm: [___________]   Lọc: [Tất cả ▼]   [⟳ Refresh]          │
├──────────┬──────────────┬────────────┬──────────┬────────┬──────────┤
│ ID       │ Tên trạm     │ Repo       │ Ngày tạo │ Trạng  │ Hành động│
├──────────┼──────────────┼────────────┼──────────┼────────┼──────────┤
│ TRAM_001 │ Trạm Xã A    │ .../sta..  │ 29/04/26 │ ✅     │ [📋] [🗑]│
│ TRAM_002 │ Trạm Xã B    │ .../sta..  │ 28/04/26 │ ✅     │ [📋] [🗑]│
│ TRAM_003 │ Trạm Huyện C │ .../sta..  │ 27/04/26 │ ❌ Rev  │ [📋]     │
└──────────┴──────────────┴────────────┴──────────┴────────┴──────────┘
```

### Hành động

| Hành động | Mô tả |
|-----------|-------|
| **📋 Copy** | Copy invite code vào clipboard |
| **🔗 Mở repo** | Link đến GitHub repo (tab mới) |
| **🗑 Revoke** | Xóa deploy key trên GitHub + đổi status = `revoked` (có confirm dialog) |

### Flow tích hợp với Tab Tạo mã kích hoạt

Khi Admin bấm "🚀 Tạo trạm" ở Tab 1 (Tạo mã kích hoạt):
1. Thực hiện flow hiện tại (tạo repo, deploy key, invite code)
2. **MỚI:** Lưu vào `stations` table
3. Hiển thị trong Tab Danh sách trạm

### Tìm kiếm & Lọc

- **Tìm kiếm:** theo station_id hoặc station_name (LIKE)
- **Lọc status:** Tất cả / Active / Revoked

## Rationale

- **SQLite local:** Đơn giản, không cần DB server riêng, đủ cho use case Admin
- **Lưu invite_code:** Admin có thể copy lại mã cũ khi trạm cần restore (đổi máy)
- **Lưu deploy_key_id:** Để revoke trực tiếp từ UI mà không cần vào GitHub
- **Extend dễ:** Thêm cột = 1 dòng ALTER TABLE, không migration phức tạp

## Related Endpoints

- Không có endpoint mới — đây là read/write trực tiếp trên SQLite local
- Tương tác với: `github_api.py` (create_deploy_key, delete_deploy_key)

## FHIR/IHE Mapping

- Resources: không có
- Phạm vi: system-level, không liên quan dữ liệu y tế

## Persona Impact

- **Persona C (Hub Admin):** người dùng chính — quản lý danh sách trạm, revoke khi cần

## Implementation Plan

1. **DB:** Tạo `hub/carevl_hub/db.py` — model + CRUD operations ✅
2. **Backend:** Update `hub/carevl_hub/gui/tab_invite.py` — sau khi tạo trạm, lưu vào DB ✅
3. **UI:** Tạo `hub/carevl_hub/gui/tab_stations.py` — render bảng + actions ✅
4. **API:** Thêm `github_api.delete_deploy_key()` ✅
5. **Sidebar:** Thêm tab mới vào `hub/carevl_hub/gui/app.py` ✅

## Files Changed

| File | Change |
|------|--------|
| `hub/carevl_hub/db.py` | Tạo mới — SQLite stations table (10 cột) |
| `hub/carevl_hub/gui/tab_invite.py` | Import db, gọi `add_station()` sau khi tạo trạm |
| `hub/carevl_hub/gui/tab_stations.py` | Tạo mới — UI bảng + actions (Copy, Mở repo, Revoke) |
| `hub/carevl_hub/gui/app.py` | Thêm tab "📋 Danh sách trạm" |
| `hub/carevl_hub/github_api.py` | Thêm `delete_deploy_key()` |

## Pending Changes

| File | Change | Status |
|------|--------|--------|
| `hub/pyproject.toml` | Thêm `st-aggrid` dependency | ✅ Done |
| `hub/carevl_hub/gui/tab_stations.py` | Chuyển từ container/columns sang AgGrid | ✅ Done |

## DB Location

- File: `hub_data/stations.db`
- Khởi tạo tự động khi import `db.py` hoặc chạy Hub app

## Implementation Notes

### Import Timing Issue (đã fix)

**Vấn đề:** Import `db.py` ở module level gây lỗi 401 Unauthorized khi validate PAT trong Streamlit.

**Nguyên nhân:** Streamlit re-runs module khi có tương tác, import chain phức tạp gây race condition với session state.

**Giải pháp:** Dùng lazy import — đưa `from carevl_hub.db import add_station` vào trong hàm `_run_create_station()` thay vì module level.

```python
# ✅ Đúng - lazy import trong hàm
def _run_create_station(...):
    from carevl_hub.db import add_station
    add_station(...)

# ❌ Sai - import ở module level
from carevl_hub.db import add_station  # Gây lỗi 401
```

### Streamlit-aggrid Migration

**Hiện tại:** UI dùng `st.container()` + `st.columns()` — thủ công, không sortable/filterable.

**Mục tiêu:** Chuyển sang `streamlit-aggrid` để có:

- Sortable columns (click header để sort)
- Filterable (filter theo cột)
- Pagination (nếu nhiều trạm)
- Selection (chọn row để action)
- Better UX

**Dependencies:**

```toml
# hub/pyproject.toml
st-aggrid = "2.1.0"  # hoặc version mới nhất
```

**Code change:**

```python
# Trước
for idx, row in enumerate(stations):
    st.markdown(f"**{row['station_id']}**")
    ...

# Sau
from st_aggrid import AgGrid, GridOptionsBuilder

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_pagination(paginationAutoPageSize=True)
gb.configure_side_bar()
gb.configure_default_column(sortable=True, filterable=True)
gridOptions = gb.build()

AgGrid(df, gridOptions=gridOptions, allow_unsafe_jscode=True)
```

**Cột hiển thị:** station_id, station_name, repo_url, created_at, status, actions (Copy/Revoke)

## Mockup Assets

- TBD: chưa có screenshot

## Related Documents

- [17. Invite Code Authentication](../ACTIVE/17_Invite_Code_Authentication.md)
- [30. Hub Auto-Provisioning: Admin PAT + SSH Deploy Key](../ACTIVE/30_Hub_Auto_Provisioning.md)
- [Hub Operator GUI (Streamlit)](hub_operator_gui.md)
- [29. Hub Operator GUI](../ACTIVE/29_Hub_Operator_Gui_Streamlit.md)