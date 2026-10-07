import os
import sys
import json
import logging
from pathlib import Path
from typing import Optional
from mcp.server.fastmcp import FastMCP
import httpx
from dotenv import dotenv_values

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s", stream=sys.stderr)
logger = logging.getLogger("mcp_server")

# 1. Initialize FastMCP
mcp = FastMCP("NY Tagging System")

# 2. Determine backend URL by reading backend_v2/.env
def get_backend_url() -> str:
    # Check environment variable first
    backend_url = os.getenv("BACKEND_URL")
    if backend_url:
        return backend_url.rstrip("/")

    # Check for backend_v2/.env file
    current_dir = Path(__file__).parent.resolve()
    for parent in [current_dir, current_dir.parent]:
        env_path = parent / "backend_v2" / ".env"
        if env_path.exists():
            try:
                env_config = dotenv_values(env_path)
                port = env_config.get("API_PORT")
                if port:
                    logger.info(f"Loaded backend port {port} from {env_path}")
                    return f"http://localhost:{port}"
            except Exception as e:
                logger.error(f"Error reading .env file at {env_path}: {e}")

    logger.warning("Could not find backend .env, defaulting to http://localhost:8001")
    return "http://localhost:8001"

BACKEND_URL = get_backend_url()
logger.info(f"Using Backend URL: {BACKEND_URL}")

def get_print_agent_url() -> str:
    print_agent_url = os.getenv("PRINT_AGENT_URL")
    if print_agent_url:
        return print_agent_url.rstrip("/")
    
    print_agent_port = os.getenv("PRINT_AGENT_PORT") or "8080"
    return f"http://localhost:{print_agent_port}"

PRINT_AGENT_URL = get_print_agent_url()
logger.info(f"Using Print Agent URL: {PRINT_AGENT_URL}")

# 3. Helper to communicate with Backend
async def call_backend(endpoint: str, method: str = "GET", params: Optional[dict] = None, json_data: Optional[dict] = None):
    url = f"{BACKEND_URL}{endpoint}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            if method == "GET":
                response = await client.get(url, params=params)
            elif method == "POST":
                response = await client.post(url, params=params, json=json_data)
            elif method == "PUT":
                response = await client.put(url, json=json_data)
            elif method == "PATCH":
                response = await client.patch(url, json=json_data)
            elif method == "DELETE":
                response = await client.delete(url)
            else:
                return {"error": f"Unsupported method: {method}"}
            
            if response.status_code >= 400:
                return {"error": f"Backend returned status {response.status_code}: {response.text}"}
            return response.json()
        except httpx.RequestError as e:
            return {"error": f"Failed to connect to backend at {url}: {str(e)}"}

async def call_print_agent(endpoint: str, method: str = "POST", json_data: Optional[dict] = None) -> dict:
    url = f"{PRINT_AGENT_URL}{endpoint}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            if method == "GET":
                response = await client.get(url)
            else:
                response = await client.post(url, json=json_data)
            
            if response.status_code != 200:
                return {"success": False, "message": f"Print Agent returned status {response.status_code}: {response.text}"}
            res_json = response.json()
            if isinstance(res_json, list):
                return {"success": True, "data": res_json}
            return res_json
        except httpx.RequestError as e:
            return {"success": False, "message": f"Failed to connect to Print Agent at {url}: {str(e)}"}

# 4. Resources
@mcp.resource("glossary://domain-glossary")
def get_domain_glossary() -> str:
    """Gets the domain glossary and vocabulary guidelines for the NY Tagging System from CONTEXT.md."""
    current_dir = Path(__file__).parent.resolve()
    for parent in [current_dir, current_dir.parent, current_dir.parent.parent]:
        context_path = parent / "CONTEXT.md"
        if context_path.exists():
            try:
                return context_path.read_text(encoding="utf-8")
            except Exception as e:
                return f"Error reading CONTEXT.md: {str(e)}"
    return "Error: CONTEXT.md not found in project workspace."

# 5. Tools
@mcp.tool()
async def get_carton_details(carton_sn: str) -> str:
    """Get the details of a Carton by its Carton SN (Serial Number), including the Carton Items inside it."""
    res = await call_backend("/api/v1/cartons/search", params={"carton_sn": carton_sn})
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def search_by_item_sn(item_sn: str) -> str:
    """Search for the Carton containing a specific scanned product (Carton Item) by its Item SN (Serial Number)."""
    res = await call_backend("/api/v1/cartons/search/item", params={"item_sn": item_sn})
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def list_products(search: str = "", limit: int = 15) -> str:
    """List configured Products in the NY Tagging System, including their packed_qty rules.
    Can filter by search keyword (for product name) and limit results to prevent overflow.
    """
    res = await call_backend("/api/v1/products")
    if isinstance(res, dict) and "error" in res:
        return json.dumps(res, indent=2, ensure_ascii=False)
    
    if not isinstance(res, list):
        return json.dumps({"error": f"Unexpected backend response type: {type(res)}"}, indent=2, ensure_ascii=False)

    # Filter products if search is provided
    filtered = []
    for p in res:
        if search and search.lower() not in p.get("item_name", "").lower():
            continue
        
        # Keep only relevant fields to avoid payload bloat
        filtered.append({
            "id": p.get("id"),
            "item_name": p.get("item_name"),
            "upc": p.get("upc"),
            "packed_qty": p.get("packed_qty"),
            "allow_partial": p.get("allow_partial")
        })
    
    # Apply limit
    limited = filtered[:limit]
    
    return json.dumps({
        "products": limited,
        "returned_count": len(limited),
        "total_count": len(filtered),
        "note": f"Showing top {limit} products. Use search keyword if looking for a specific item." if len(filtered) > limit else ""
    }, indent=2, ensure_ascii=False)


@mcp.tool()
async def get_system_health() -> str:
    """Get the health status of the NY Tagging System backend and check if the BarTender engine is ready."""
    res = await call_backend("/api/v1/health")
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def reprint_carton(carton_sn: str, print_mode: str, printer_name: str, template_path: str = "") -> str:
    """Reprint a Carton label by its Carton SN.
    
    Parameters:
      carton_sn: The unique Carton SN (Serial Number) to reprint.
      print_mode: The printing mode to use. Must be either 'local' (prints via client print agent at http://localhost:8080) or 'server' (prints directly on server's BarTender COM engine).
      printer_name: The name of the target printer. Ask the user to choose from the local or server printer list first (call get_local_printers() or get_server_printers()) if they did not specify one.
      template_path: Optional custom template path (.btw file) override.
    """
    # Step 1: Find Carton by SN to get its ID
    carton = await call_backend("/api/v1/cartons/search", params={"carton_sn": carton_sn})
    if "error" in carton:
        return json.dumps({"error": f"Could not find Carton with SN {carton_sn}: {carton['error']}"}, indent=2, ensure_ascii=False)
    
    carton_id = carton.get("id")
    if not carton_id:
        return json.dumps({"error": f"Carton ID not found for SN {carton_sn} in response: {carton}"}, indent=2, ensure_ascii=False)

    # Step 2: Trigger reprint backend endpoint to create the database records and generate BTXML
    params = {}
    if printer_name:
        params["printer_name"] = printer_name
    if template_path:
        params["template_path"] = template_path

    new_carton = await call_backend(f"/api/v1/print/carton/{carton_id}/reprint", method="POST", params=params)
    if "error" in new_carton:
        return json.dumps({"error": f"Failed to register reprint on backend: {new_carton['error']}"}, indent=2, ensure_ascii=False)

    new_carton_id = new_carton.get("id")
    btxml = new_carton.get("btxml")
    if not new_carton_id or not btxml:
        return json.dumps({"error": f"Reprint Carton ID or BTXML not returned by backend: {new_carton}"}, indent=2, ensure_ascii=False)

    # Step 3: Trigger the physical print based on the selected mode
    mode = print_mode.lower().strip()
    if mode == "local":
        print_agent_req = {
            "xml_content": btxml,
            "printer_name": printer_name or None
        }
        logger.info(f"Sending print job to Local Print Agent at {PRINT_AGENT_URL}/print")
        print_res = await call_print_agent("/print", json_data=print_agent_req)
        
        # Update status on backend
        if print_res.get("success"):
            update_res = await call_backend(
                f"/api/v1/print/carton/{new_carton_id}/status",
                method="PATCH",
                json_data={"status": "SUCCESS"}
            )
            return json.dumps({
                "success": True,
                "message": f"Successfully reprinted carton {carton_sn} via Local Print Agent.",
                "carton_details": update_res,
                "print_agent_response": print_res
            }, indent=2, ensure_ascii=False)
        else:
            update_res = await call_backend(
                f"/api/v1/print/carton/{new_carton_id}/status",
                method="PATCH",
                json_data={"status": "FAILED"}
            )
            return json.dumps({
                "success": False,
                "error": f"Local print agent failed: {print_res.get('message')}",
                "carton_details": update_res
            }, indent=2, ensure_ascii=False)
            
    elif mode == "server":
        server_print_params = {"printer_name": printer_name}
        logger.info(f"Sending print job to Central Server BarTender engine")
        print_res = await call_backend(
            f"/api/v1/print/carton/{new_carton_id}/server-print",
            method="POST",
            params=server_print_params
        )
        
        if "error" in print_res:
            return json.dumps({"error": f"Server print failed: {print_res['error']}"}, indent=2, ensure_ascii=False)
            
        return json.dumps({
            "success": print_res.get("success", False),
            "message": print_res.get("message", "Processed reprint job on server"),
            "carton_details": new_carton,
            "print_result": print_res
        }, indent=2, ensure_ascii=False)
    else:
        return json.dumps({"error": f"Invalid print_mode '{print_mode}'. Must be 'local' or 'server'."}, indent=2, ensure_ascii=False)

@mcp.tool()
async def server_print_carton(carton_sn: str, printer_name: str = "", fallback_template_path: str = "") -> str:
    """Print a Carton label directly from the server's BarTender COM engine without using a separate client agent."""
    # Step 1: Find Carton by SN to get its ID
    carton = await call_backend("/api/v1/cartons/search", params={"carton_sn": carton_sn})
    if "error" in carton:
        return json.dumps({"error": f"Could not find Carton with SN {carton_sn}: {carton['error']}"})
    
    carton_id = carton.get("id")
    if not carton_id:
        return json.dumps({"error": f"Carton ID not found for SN {carton_sn} in response: {carton}"})

    # Step 2: Trigger print via POST /api/v1/print/carton/{carton_id}/server-print
    params = {}
    if printer_name:
        params["printer_name"] = printer_name
    if fallback_template_path:
        params["fallback_template_path"] = fallback_template_path

    res = await call_backend(f"/api/v1/print/carton/{carton_id}/server-print", method="POST", params=params)
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def get_packaging_statistics(start_date: str, end_date: str) -> str:
    """Get packaging statistics, including total cartons, success/failed rate, reprint rate,
    total items scanned, daily breakdown, and product breakdown.
    Both start_date and end_date are required in YYYY-MM-DD format.
    """
    res = await call_backend("/api/v1/cartons/statistics", params={"start_date": start_date, "end_date": end_date})
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def get_job_order_statistics(job_order: str) -> str:
    """Get packaging statistics and detailed carton list for a specific Job Order."""
    res = await call_backend(f"/api/v1/cartons/job-order/{job_order}/statistics")
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def get_local_printers() -> str:
    """Get the list of active physical printers connected to the local station."""
    res = await call_print_agent("/printers", method="GET")
    return json.dumps(res, indent=2, ensure_ascii=False)

@mcp.tool()
async def get_server_printers() -> str:
    """Get the list of physical printers connected to the central backend server."""
    res = await call_backend("/api/v1/print/printers")
    return json.dumps(res, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    mcp.run()
