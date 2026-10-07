# Architecture

## System Overview
The NY Tagging System is a hybrid web application designed for high-speed industrial packing and labeling. It follows a multi-tier architecture:

1.  **Frontend (UI)**: A Vue 3 + TypeScript SPA that provides the operator interface for scanning and monitoring.
2.  **Backend (API)**: A modular FastAPI service (v2) that handles business logic, serial number generation, and database interactions.
3.  **Database (Persistence)**: Microsoft SQL Server storing master data (Customers, Products) and transaction logs (Cartons, Items).
4.  **Local Print Agent (Execution)**: A standalone Python agent running on the client workstation to interact directly with BarTender via COM.

## Hybrid Printing Workflow
To ensure reliable printing to local USB/Network printers without browser prompts:
-   **Backend Role**: Generates a BarTender XML (BTXML) script containing all dynamic data (Item Name, S/N, QR Code).
-   **Frontend Role**: Receives the BTXML and relays it to the local agent's HTTP port (1234).
-   **Agent Role**: Receives the script, automates BarTender (COM), checks printer status, and triggers the physical print.

## Key Design Principles
-   **Concurrency Safety**: Uses SQLAlchemy `with_for_update()` on sequence generation to prevent duplicate Carton S/Ns.
-   **Feature Modularity**: Uses a feature-sliced directory structure in both backend and frontend for scalability.
-   **Type Safety**: Full TypeScript integration in the frontend to catch errors early.
-   **Rich Aesthetics**: Premium UI design with dark mode support and responsive layouts using Tailwind CSS 4.
