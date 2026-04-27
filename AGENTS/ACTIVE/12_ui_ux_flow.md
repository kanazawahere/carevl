# UI/UX Data Flow: Intake to Delayed Results (Sprint 5)

## Objective
Analyze and map the data movement from the initial patient intake (Persona A) to the delayed results entry (Persona C), adhering to Persona-Centric design and FHIR/IHE standards (specifically IHE PIXm).

## 1. Persona A: "Tiếp nhận" (Initial Intake)
*   **Role:** Operator/Receptionist at the Site.
*   **Sidebar Item:** `1. Tiếp nhận mới`
*   **Action:**
    *   Scans patient ID (CCCD).
    *   System generates a deterministic `UUIDv5` for the Encounter using `SiteID + CCCD + Timestamp`.
    *   System maps this UUID to a physical barcode sticker (`sticker_id`).
*   **Data Model (FHIR Mapping):**
    *   **Patient:** Created or retrieved based on CCCD.
    *   **Encounter:** Created with the generated `UUIDv5`, linked to the `Patient`, and assigned the `sticker_id`.
*   **Database Implication (IHE PIXm Support):**
    *   A robust linking mechanism must exist where a given `sticker_id` quickly resolves to the Encounter UUID, which in turn maps back to the Patient identity (CCCD).

## 2. Persona B: "Lâm sàng" (Clinical Operations)
*   **Role:** Clinician / Nurse.
*   **Sidebar Items:** `2. Lượt khám`, `3. Hồ sơ bệnh nhân`
*   **Action:**
    *   Patient moves through the queue.
    *   Clinicians record immediate vital signs.
*   **Data Model:**
    *   **Observation:** Vital signs linked to the Encounter UUID.

## 3. Persona C: "Nhập liệu" (Data Entry - Delayed / Individual Tracker)
*   **Role:** Contributor / Lab Technician.
*   **Sidebar Item:** `5. Cập nhật kết quả` (Crucially distinct from `4. Nhập liệu (Aggregate)`)
*   **Action:**
    *   Delayed results (e.g., Lab tests, X-rays) arrive later.
    *   The technician uses the physical sticker (`sticker_id`) or the digital identifier.
    *   The system *must* cleanly separate this individual data point entry from bulk reporting.
*   **Data Model (FHIR Mapping):**
    *   **DiagnosticReport:** Results entered are linked back to the specific Encounter via the scanned `sticker_id`.
*   **UI/UX Requirement:**
    *   When Persona C is in "Cập nhật kết quả", the UI must strictly isolate this context. They must not accidentally enter the "Tiếp nhận" flow. The active Sidebar state must clearly indicate their current location in the application.

## 4. Separation of Concerns (Data-Side)
*   **Individual Tracker (`5. Cập nhật kết quả`):** Transactional data linked to a specific Encounter (`sticker_id` -> `uuid`). FHIR `DiagnosticReport` / `Observation`.
*   **Aggregate Data (`4. Nhập liệu (Aggregate)`):** Bulk or summarized data entry (e.g., DHIS2 compatible). FHIR `MeasureReport`. This does *not* deal with individual `sticker_id`s.

## 5. Summary Flow
`CCCD (Patient)` -> `Intake` -> `[UUID + Sticker_ID] (Encounter)` -> `Clinical Observations` -> ...time passes... -> `Scan Sticker_ID` -> `Delayed Result Entry (DiagnosticReport)`.