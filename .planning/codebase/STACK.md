# Technology Stack

## Backend
- **Framework**: FastAPI (Python 3.12+)
- **Database ORM**: SQLAlchemy 2.0
- **Database Driver**: pyodbc (ODBC Driver 18 for SQL Server)
- **Environment Management**: python-dotenv
- **Server**: Uvicorn
- **Package Manager**: uv

## Frontend
- **Framework**: Vue 3 (Composition API)
- **Language**: TypeScript 6.0+
- **Build Tool**: Vite 8.0+
- **State Management**: Pinia
- **Styling**: Tailwind CSS 4.0
- **HTTP Client**: Axios
- **Icons**: Lucide-Vue-Next
- **Internationalization**: vue-i18n

## Client Agent (Print Agent)
- **Language**: Python
- **Automation**: pywin32 (win32com) for BarTender COM automation
- **Communication**: HTTP Server (built-in `http.server`)
- **Printer Management**: win32print

## Infrastructure
- **Web Application Server**: Windows (required for BarTender COM)
- **Database**: Microsoft SQL Server
- **Labeling**: BarTender Integration / SDK (COM)
- **Containerization**: Docker (optional, for non-printing components)
