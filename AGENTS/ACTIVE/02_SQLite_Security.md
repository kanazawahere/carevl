# SQLite Security & Snapshots

## Status
[Active]

## Context
Tram can luu du lieu y te theo kieu offline-first, van ghi duoc khi nhieu nguoi thao tac, va khi co mang thi phai dong goi an toan truoc khi day ve Hub.

## Decision
Dung SQLite local DB voi lop bao ve va snapshot ro rang.

1. Runtime DB la SQLite.
2. Bat buoc WAL qua SQLAlchemy connection event: `PRAGMA journal_mode=WAL`.
3. Tao snapshot bang `sqlite3.backup()` de lay ca du lieu nam trong WAL.
4. Ma hoa snapshot thanh `.db.enc` bang AES-256-CBC qua `cryptography`, key lay tu `.env`.
5. Chay backup tu dong qua APScheduler moi 15 phut, xoa file cu hon 7 ngay.

## Rationale
WAL giam loi `database is locked` khi doc/ghi dong thoi. Backup API dam bao snapshot nhat quan, khong bo sot du lieu chi vi copy file `.db` tho. AES-256 giu file an toan khi van chuyen hoac luu tam.

## Related Documents
- [07. Active Sync Protocol: The Encrypted SQLite Blob](07_active_sync_protocol.md)
- [14. Bootstrap Infrastructure: One-Liner Setup](14_Bootstrap_Infrastructure.md)
- [33. Invite Code Authentication: Deploy Key First](33_Invite_Code_Authentication_Deploy_Key_First.md)
