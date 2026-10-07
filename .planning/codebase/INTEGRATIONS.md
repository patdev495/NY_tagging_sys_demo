# Integrations

## Backend <-> MSSQL
- Connected via `sqlalchemy` 2.0 and `pyodbc`.
- Database schema managed via feature-specific `models.py`.
- Automated table creation on startup in `main.py`.

## Backend <-> Client Agent (Print Agent)
- **Handoff**: The backend returns BTXML to the frontend.
- **Relay**: The frontend sends this XML to `http://localhost:1234/print`.
- **Local Isolation**: This setup allows the web app to trigger hardware actions without browser security restrictions.

## Client Agent <-> BarTender
- Uses `win32com.client` (Dispatch) to interface with the `BarTender.Application` COM object.
- Maps JSON/XML data to BarTender "Named SubStrings".
- Handles printer selection and job queuing.

## Frontend <-> Backend
- **REST API**: Communicates over JSON via Axios.
- **V2 API**: All routes prefixed with `/api/v1`.
- **Deployment**: Backend serves the production frontend build from `frontend_v2/dist`.

## Hardware Integrations
- **Scanners**: Handheld USB/Bluetooth scanners acting as HID (Keyboard) input.
- **Printers**: Industrial label printers (Zebra, TSC, Honeywell) managed via Windows print drivers.
