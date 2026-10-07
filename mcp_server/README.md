# NY Tagging System MCP Server

Model Context Protocol (MCP) server for querying and managing the **NY Tagging System**. This server runs locally via standard input/output (stdio) and integrates directly with your AI development tools.

---

## Prerequisites

1. **Python 3.12+**
2. **uv** (Fast Python package manager)
3. **NY Tagging System Backend V2** running on `http://localhost:8001` (or another port specified in `backend_v2/.env`).

---

## Features

### Resources
- `docs/domain-glossary`: Dynamically feeds the domain terms defined in `CONTEXT.md` to the AI client to ensure vocabulary consistency.

### Tools
- `get_system_health`: Checks backend API and BarTender Engine initialization status.
- `list_products`: Retrieves all products and their configurations (e.g. `packed_qty`, `allow_partial`).
- `get_carton_details`: Queries a physical packaging carton by its **Carton SN**.
- `search_by_item_sn`: Traces which carton contains a specific scanned serial number (**Item SN**).
- `reprint_carton`: Creates a duplicate carton record with `is_reprint=1` to repeat label printing without incrementing indices.
- `server_print_carton`: Triggers the local Windows BarTender COM printing engine directly.

---

## Client Integration Guide

### 1. Claude Desktop (Windows)

Open your Claude Desktop configuration file (typically located at `%APPDATA%\Claude\claude_desktop_config.json`) and add the server definition to the `mcpServers` block:

```json
{
  "mcpServers": {
    "ny-tagging-system": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "D:\\Workspace\\NY_tagging_sys\\mcp_server",
        "python",
        "D:\\Workspace\\NY_tagging_sys\\mcp_server\\server.py"
      ],
      "env": {
        "BACKEND_URL": "http://localhost:8001"
      }
    }
  }
}
```

*Note: Replace `D:\\Workspace\\NY_tagging_sys` with the absolute path to your workspace directory if it is different.*

Restart Claude Desktop, and you should see the plug/connections icon representing that the MCP Server is connected.

---

### 2. Cursor IDE

1. Open **Cursor Settings** (`Ctrl + ,` or click gear icon).
2. Go to **Features** -> **MCP**.
3. Click **+ Add New MCP Server**.
4. Enter the details:
   - **Name**: `NY-Tagging-System`
   - **Type**: `command`
   - **Command**:
     ```bash
     uv run --project D:\Workspace\NY_tagging_sys\mcp_server python D:\Workspace\NY_tagging_sys\mcp_server\server.py
     ```
5. Click **Save**.

---

### 3. VS Code (Cline / Roo Code Extensions)

Add the following config to your extension's MCP configuration settings (`cline_mcp_settings.json` or `roo_mcp_settings.json`):

```json
{
  "mcpServers": {
    "ny-tagging-system": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "D:\\Workspace\\NY_tagging_sys\\mcp_server",
        "python",
        "D:\\Workspace\\NY_tagging_sys\\mcp_server\\server.py"
      ],
      "env": {
        "BACKEND_URL": "http://localhost:8001"
      }
    }
  }
}
```
