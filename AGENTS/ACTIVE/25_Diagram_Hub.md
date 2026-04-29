# Diagram Hub: State Machine & Dataflow Index

## Status
[Active]

## Context
Team can mot diem vao duy nhat de tim tat ca so do ky thuat (state machine, workflow, architecture) va bang lien quan (schema contracts, dataflow transactions), de ca nguoi va AI khong bo sot.

## Decision
Dung file nay lam **index trung tam** cho toan bo diagram ky thuat.

### Cach dung
1. Mo file nay truoc de chon dung so do.
2. Neu can logic chi tiet, vao doc state machine + contracts/dataflow doc.
3. Neu can artifact de trinh bay, mo SVG trong `AGENTS/ASSETS/`.

### Canonical visualization docs
- [24. Verified State Machine Diagramming](24_Verified_State_Machine_Diagramming.md)
- [18. Two-App Architecture: Edge vs Hub](18_Two_App_Architecture.md)
- [11. Workflow](11_Workflow.md)

### Diagram Index
| Diagram ID | Scope | Source Document | Asset / Render | Contracts & Dataflow |
|---|---|---|---|---|
| `edge_architecture_v1` | Edge app architecture | [18. Two-App Architecture](18_Two_App_Architecture.md) | [edge_app_architecture.svg](../ASSETS/edge_app_architecture.svg) | N/A |
| `hub_architecture_v1` | Hub app architecture | [18. Two-App Architecture](18_Two_App_Architecture.md) | [hub_app_architecture.svg](../ASSETS/hub_app_architecture.svg) | N/A |
| `overview_e2e_v1` | End-to-end operational flow | [TUTORIAL.md](../../TUTORIAL.md) | [overview_end_to_end.svg](../ASSETS/overview_end_to_end.svg) | N/A (user-facing overview) |
| `gateway_setup_sm_v1` | Gateway setup state machine | [24. Verified State Machine](24_Verified_State_Machine_Diagramming.md) | Mermaid in doc | Schema + Dataflow trong doc 24 |
| `auth_example_sm_v1` | Auth state machine example | [24. Verified State Machine](24_Verified_State_Machine_Diagramming.md) | Mermaid in doc | Schema + Dataflow trong doc 24 |

### Authoring rules (short)
- Diagram nguon uu tien Mermaid cho versioning.
- State machine transition label chi giu action ngan.
- Schema contracts + dataflow transactions luon tach bang Markdown ben duoi diagram.
- Artifact SVG luu trong `AGENTS/ASSETS/`.

## Rationale
Co index trung tam giup:
- Nguoi moi vao tim dung so do nhanh.
- AI agent co diem vao ro rang, giam bo sot khi scan docs.
- Dam bao moi so do co nguon, asset, va thong tin lien ket ro.

## Related Documents
- [24. Verified State Machine Diagramming](24_Verified_State_Machine_Diagramming.md)
- [18. Two-App Architecture: Edge vs Hub](18_Two_App_Architecture.md)
- [TUTORIAL.md](../../TUTORIAL.md)
