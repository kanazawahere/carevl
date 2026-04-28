# CareVL: Admin Hub App Design Proposal

## 1. Overview
The **Admin Hub App** is a centralized web dashboard intended for the Provincial/Central health management level (Hub). While the current CareVL edges (local clinics/mobile units) operate offline and push encrypted `.db.enc` snapshots to GitHub Releases, the Hub App serves as the destination for these snapshots. Its primary purpose is to aggregate, decrypt, and visualize the incoming data.

## 2. Core Use Cases
1. **Key Management & Decryption:** The Hub Admin holds the `Private Encryption Key`. The app will download encrypted snapshots from the centralized GitHub Repository, authenticate the user, and securely decrypt the `.db.enc` files back into standard SQLite files.
2. **Data Aggregation (DuckDB):** Instead of standard OLTP SQLite, the Hub App will utilize **DuckDB** to quickly ingest, combine, and query across dozens of edge SQLite databases simultaneously.
3. **Global Dashboard & Reporting:** A central UI to view epidemiological reports, equipment status, and aggregated MeasureReports across all regions (e.g., SITE_IDs).
4. **Edge Management:** Monitor the sync status, last active time, and version compliance of all deployed Edge clients.

## 3. Architecture & Tech Stack
*   **Backend:** FastAPI (Python >= 3.11).
*   **Database (Analytics):** `DuckDB` (ideal for cross-file queries on multiple SQLite `.db` files without needing a heavy ETL pipeline).
*   **Frontend:** Jinja2 + HTMX + TailwindCSS (consistent with the Edge stack).
*   **Authentication:** GitHub OAuth (Hub Admins must be verified members of the central GitHub Organization).
*   **Deployment:** Cloud-hosted (e.g., Vercel, Render, or a VPS) with internet access, unlike the offline-first Edge nodes.

## 4. Workflows

### A. Snapshot Ingestion Flow
1. **Trigger:** A background task (or webhook) polls the GitHub Repository for new Releases containing `.db.enc` artifacts.
2. **Download:** The Hub app downloads the artifact securely using a GitHub PAT.
3. **Decryption:** The Hub App uses the securely stored Hub Private Key (loaded in memory via admin input or secure KMS) to decrypt the snapshot using AES-256 (via the `cryptography` library).
4. **Mounting:** The decrypted SQLite database is saved in a temporary/secure volume and "attached" to the central DuckDB instance (e.g., `ATTACH 'edge_01.db' AS edge_01`).

### B. Security Protocol
*   **No Persistent Private Key:** To maximize security, the Private Key used for decryption is never hardcoded. The Hub Admin must enter it via a secure PIN/Password input upon logging into the Hub App, or it must be managed by a strict Secrets Manager.
*   **Data Ephemerality:** Raw patient data (PII) is queried on the fly or anonymized before being cached in the Hub's materialized views.

## 5. Proposed UI Layout

*   **Login Screen:** GitHub OAuth -> Enter Private Key (to unlock decryption module).
*   **Dashboard View:**
    *   Top Cards: Total Edges Synced Today, Total Encounters, Alerts.
    *   Map/Chart: Distribution of cases by `SITE_ID`.
*   **Edge Management View:** A table listing all connected sites, their last snapshot timestamp, and GitHub release link.
*   **Query Builder (Admin Only):** A secure SQL interface (powered by DuckDB) to run custom analytics across all synced nodes.

## 6. Next Steps for Implementation
1. **Create the Project Structure:** Set up a separate directory or repository (e.g., `carevl-hub`) to separate the Hub App logic from the Edge App.
2. **Implement DuckDB Adapter:** Write the logic to attach multiple SQLite files into DuckDB.
3. **Build the Decryption Worker:** Implement the script that pulls `.db.enc` from GitHub and decrypts it.
4. **Develop the UI:** Create the Dashboard and Edge Management views.
