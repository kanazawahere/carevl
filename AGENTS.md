# Continuous Memory Vault - Ban do Kien truc CareVL

> **Luat goc**: Day la bo nho lau dai. Doi thiet ke cot loi thi khong sua file cu. Tao file moi trong `ACTIVE`, day file cu qua `ARCHIVE`. Moi tai lieu theo chuan [ADR (Architecture Decision Record)](https://adr.github.io/).

## Quy tac viet tai lieu (BAT BUOC)

1. **Moi tai lieu ky thuat phai nam trong `AGENTS/`**
   - `AGENTS/ACTIVE/`: kien truc va quyet dinh dang dung
   - `AGENTS/FEATURES/`: tai lieu tinh nang nghiep vu
   - `AGENTS/ARCHIVE/`: tai lieu da bo, de giai thich vi sao khong dung
   - `AGENTS/ASSETS/`: tat ca anh, mockup, diagram, SVG

2. **Khong tao file `.md` hay thu muc anh lung tung**
   - ❌ Sai: `scripts/README.md`, `docs/guide.md`, `SETUP.md`, `images/`, `assets/`
   - ✅ Dung: `AGENTS/ACTIVE/16_Setup_Guide.md`, `AGENTS/ASSETS/diagram.svg`
   - **Neu can tao doc thi phai:**
     - Tao trong `AGENTS/ACTIVE/` hoac `AGENTS/FEATURES/`
     - Them link vao `AGENTS.md`
     - Khong duoc tao file `.md` roi rac ngoai `AGENTS/`

3. **Moi tai lieu moi phai co link trong `AGENTS.md`**
   - Them vao `ACTIVE`, `FEATURES`, hoac `ARCHIVE`
   - Phai de tim, de quet
   - Khong co trong `AGENTS.md` = khong ton tai

4. **Format theo ADR**
   - `## Status`: [Active], [Active - Implemented], [Deprecated], [Planned]
   - `## Context`: boi canh, van de
   - `## Decision`: quyet dinh ky thuat
   - `## Rationale`: vi sao chon cach nay
   - `## Related Documents`: link lien quan

5. **Doi thiet ke cot loi**
   - Khong sua file cu
   - Tao file moi trong `ACTIVE` voi so tiep theo
   - Day file cu qua `ARCHIVE`
   - Cap nhat link trong `AGENTS.md`

6. **Khi file ADR cu da bi thay doi boi thiet ke moi, uu tien giu so cu lam `deprecated pointer`**
   - Neu file cu dang duoc link rong, **khong nen** viet de no tiep tuc gia lam truth source
   - Thay vao do:
     - doi `## Status` thanh `[Deprecated]`
     - ghi ro file cu mo ta flow nao da het hieu luc
     - tro sang ADR moi trong `ACTIVE`
   - Muc tieu: **giu so cu de khong vo link lich su**, nhung khong de nguoi doc hieu nham flow cu la flow dang song
   - Chi day file cu qua `ARCHIVE` khi chac chan link cu/tham chieu cu khong con can giu on dinh

## Development Environment (Bat buoc)

**Python = uv, uv = python**

Project nay dung `uv` lam package manager. Moi lenh Python phai chay qua `uv`:

```bash
# ❌ SAI - Khong dung truc tiep
python script.py
pip install package

# ✅ DUNG - Dung qua uv
uv run python script.py
uv pip install package
uv sync
```

**Ly do:**
- `uv` quan ly virtual environment tu dong
- Dam bao dependencies nhat quan
- Nhanh hon pip
- Khong conflict voi Python system

## Feature Syncing Protocol (Bat buoc)
**Feature doi. Doc phai doi theo.**

O buoc finalize, truoc `submit`, agent phai lam:

1. Chay `git diff --name-only` de quet file da doi.
2. Tim file `.md` ung voi feature trong `AGENTS/FEATURES/` nhu `auth.md`, `sync.md`. Chua co thi tao.
3. Cap nhat ro `Status`, endpoint lien quan, va logic nghiep vu vua doi.

**Neu dong vao mockup anh:**
- Tao hoac sua anh trong `AGENTS/ASSETS/` thi phai sua moi link tham chieu trong file `.md`
- Dung `git grep "ten_file_anh"` de tim moi noi dang tro toi
- Commit anh va link cung luc, tranh vo link

---

## SOP & Resources
- [Cam nang Thiet ke Hinh anh (Image Generation Bible)](AGENTS/IMAGE_GUIDE.md)

## START HERE - VISUALIZATION (SVG + MERMAID + TABLES)
- [26. Visualization Catalog: SVG, Mermaid & Tables](AGENTS/ACTIVE/26_Visualization.md)
- [24. Verified State Machine Diagramming](AGENTS/ACTIVE/24_Verified_State_Machine_Diagramming.md)

## START HERE - DOMAIN DATA (NGUOI TRUOC, MAY SAU)
- [27. Phạm vi thu thập dữ liệu nghiệp vụ](AGENTS/ACTIVE/27_Business_Data_Intake_Scope.md) — phạm vi thu thập, đối tượng, mô-đun; đối chiếu trước [09. Phase 2 Schema](AGENTS/ACTIVE/09_Phase2_Schema_Spec.md)

---

## ACTIVE (Tinh nang & Kien truc dang chay)
Quyet dinh dang song cua he thong.

- [01. FastAPI Core Architecture](AGENTS/ACTIVE/01_FastAPI_Core.md)
- [02. SQLite Security & Snapshots](AGENTS/ACTIVE/02_SQLite_Security.md)
- [03. Web UI & HTMX Interaction](AGENTS/ACTIVE/03_Web_UI_HTMX.md)
- [04. Development Guidelines & Troubleshooting](AGENTS/ACTIVE/04_Development_Guidelines.md)
- [07. Active Sync Protocol: The Encrypted SQLite Blob](AGENTS/ACTIVE/07_active_sync_protocol.md)
- [08. Hướng dẫn Admin](AGENTS/ACTIVE/08_Huong_Dan_Admin.md)
- [09. Phase 2 Schema Spec](AGENTS/ACTIVE/09_Phase2_Schema_Spec.md)
- [10. Quy chế vận hành](AGENTS/ACTIVE/10_Quy_Che_Van_Hanh.md)
- [11. Workflow](AGENTS/ACTIVE/11_Workflow.md)
- [12. UI/UX Data Flow: Intake to Delayed Results](AGENTS/ACTIVE/12_ui_ux_flow.md)
- [13. AWARE-SAVE Protocol: Visual Dirty State Management](AGENTS/ACTIVE/13_Aware_Save_Protocol.md)
- [14. Bootstrap Infrastructure: One-Liner Setup](AGENTS/ACTIVE/14_Bootstrap_Infrastructure.md)
- [15. Hub Aggregation: DuckDB Analytics Pipeline](AGENTS/ACTIVE/15_Hub_Aggregation.md)
- [16. Testing Guidelines](AGENTS/ACTIVE/16_Testing_Guidelines.md)
- [17. Invite Code Authentication: Fine-grained PAT Provisioning](AGENTS/ACTIVE/17_Invite_Code_Authentication.md)
- [18. Two-App Architecture: Edge vs Hub](AGENTS/ACTIVE/18_Two_App_Architecture.md)
  - 📊 [Edge App Architecture Diagram](AGENTS/ASSETS/edge_app_architecture.svg)
  - 📊 [Hub App Architecture Diagram](AGENTS/ASSETS/hub_app_architecture.svg)
- [19. Phase 2 Migration Guide](AGENTS/ACTIVE/19_Phase2_Migration_Guide.md)
- [20. Monorepo Migration Complete](AGENTS/ACTIVE/20_Monorepo_Migration_Complete.md)
- [21. API Specification](AGENTS/ACTIVE/21_API_Specification.md)
- [22. Deployment Guide: Edge & Hub](AGENTS/ACTIVE/22_Deployment_Guide.md)
- [23. Authentication Testing Guide](AGENTS/ACTIVE/23_Auth_Testing_Guide.md)
- [24. Verified State Machine Diagramming](AGENTS/ACTIVE/24_Verified_State_Machine_Diagramming.md)
- [26. Visualization Catalog: SVG, Mermaid & Tables](AGENTS/ACTIVE/26_Visualization.md)
- [27. Phạm vi thu thập dữ liệu nghiệp vụ (người trước, kỹ thuật sau)](AGENTS/ACTIVE/27_Business_Data_Intake_Scope.md)
- [28. Edge: Phạm vi Cài đặt trạm sau provision (`/settings`)](AGENTS/ACTIVE/28_Edge_Station_Settings_Scope.md)
- [29. Hub Operator GUI (Streamlit)](AGENTS/ACTIVE/29_Hub_Operator_Gui_Streamlit.md)
- [30. Hub Auto-Provisioning: Device Flow + Classic PAT](AGENTS/ACTIVE/30_Hub_Auto_Provisioning.md)
- [31. Snapshot Upload via GitHub Actions (không PAT trên trạm)](AGENTS/ACTIVE/31_Snapshot_Upload_Via_GitHub_Actions.md)
- [32. Hub Download & Process After GitHub Actions Release](AGENTS/ACTIVE/32_Hub_Download_And_Process_After_Actions.md)
- [33. Invite Code Authentication: Deploy Key First](AGENTS/ACTIVE/33_Invite_Code_Authentication_Deploy_Key_First.md)
- [34. Active Sync via Git Push and GitHub Actions](AGENTS/ACTIVE/34_Active_Sync_Via_Git_Push_And_Actions.md)

---

## FEATURES LEDGER (10 chuc nang Sidebar)
- [Sidebar UI Architecture](AGENTS/FEATURES/sidebar_ui.md)
- [1. Tiếp nhận mới](AGENTS/FEATURES/1_tiep_nhan_moi.md)
- [2. Lượt khám](AGENTS/FEATURES/2_luot_kham.md)
- [3. Hồ sơ bệnh nhân](AGENTS/FEATURES/3_ho_so_benh_nhan.md)
- [4. Nhập liệu (Aggregate)](AGENTS/FEATURES/4_nhap_lieu_aggregate.md)
- [5. Cập nhật kết quả](AGENTS/FEATURES/5_cap_nhat_ket_qua.md)
- [6. Báo cáo](AGENTS/FEATURES/6_bao_cao.md)
- [7. Xuất dữ liệu Hub](AGENTS/FEATURES/7_xuat_du_lieu_hub.md)
- [8. Liên thông (Audit)](AGENTS/FEATURES/8_lien_thong_audit.md)
- [9. Cài đặt trạm](AGENTS/FEATURES/9_cai_dat_tram.md)
- [10. Giới thiệu](AGENTS/FEATURES/10_gioi_thieu.md)
- [Auth Gateway (deprecated — thay Invite Code)](AGENTS/FEATURES/auth_gateway.md)
- [QR Code Provisioning (Thẻ bài điện tử)](AGENTS/FEATURES/qr_provisioning.md)
- [Hub Operator GUI (Streamlit)](AGENTS/FEATURES/hub_operator_gui.md)
- [Hub - Danh sách trạm (Station Registry)](AGENTS/FEATURES/hub_danh_sach_tram.md)

---

## ARCHIVE (Lich su & Tinh nang da thay)
Quyet dinh da bo. Giu lai de biet vi sao khong di huong cu.

- [05. Legacy CustomTkinter App](AGENTS/ARCHIVE/05_Legacy_Tkinter_App.md)
- [06. Legacy OMR Pipeline](AGENTS/ARCHIVE/06_Legacy_OMR_Pipeline.md)
- [17. GitHub Device Flow Authentication (Deprecated)](AGENTS/ARCHIVE/17_GitHub_Device_Flow.md) - thay boi Invite Code Authentication
- [25. Diagram Hub (Deprecated)](AGENTS/ARCHIVE/25_Diagram_Hub.md) - thay boi Visualization Catalog

---

*Cap nhat lan cuoi: 2026-05-01 12:05:00*
