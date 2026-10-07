import os
import json
import logging
import subprocess
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel
import xml.etree.ElementTree as ET

# Import the unified COM app singleton
from bartender_com import bt_com_app

# Import Scale Manager
try:
    from scale.manager import scale_manager
except ImportError:
    from .scale.manager import scale_manager

# Logging Setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("PrintAgent")

app = FastAPI(title="NY Print Agent V2 (Unified COM & Scale Engine)")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize BarTender and Scale on startup
@app.on_event("startup")
def startup_event():
    logger.info("Starting up Print Agent...")
    success = bt_com_app.start()
    if success:
        logger.info("BarTender COM Engine successfully started on agent.")
    else:
        logger.warning("BarTender COM Engine failed to start on agent. Will retry lazily on print jobs.")
    
    try:
        scale_manager.load_config()
        scale_manager.start()
        logger.info("Scale Manager successfully initialized.")
    except Exception as e:
        logger.warning(f"Scale Manager initialization notice: {e}")

@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down Print Agent...")
    try:
        scale_manager.stop()
    except Exception:
        pass

# === Schemas ===
class PrintRequest(BaseModel):
    xml_content: str
    printer_name: Optional[str] = None
    local_template_dir: Optional[str] = None

class ScaleConfigRequest(BaseModel):
    port: Optional[str] = None
    baudrate: Optional[int] = None
    hotkey: Optional[str] = None
    auto_connect: Optional[bool] = None

class OpenTemplateRequest(BaseModel):
    folder: Optional[str] = None
    filename: str

class OpenDirRequest(BaseModel):
    folder: Optional[str] = None

# === Endpoints ===

@app.get("/status")
@app.get("/health")
def get_status():
    return {
        "status": "online", 
        "mode": "COM", 
        "version": "2.3.0",
        "bartender_ready": bt_com_app.is_initialized,
        "scale_status": scale_manager.get_status()
    }

@app.get("/printers")
def get_printers():
    """Lấy danh sách máy in từ hệ thống"""
    printers_list = bt_com_app.get_printers()
    return [p["name"] for p in printers_list]

@app.get("/check-dir")
def check_directory(path: str = ""):
    logger.info(f"Checking directory: {path}")
    normalized_path = os.path.normpath(path)
    exists = os.path.exists(normalized_path) and os.path.isdir(normalized_path)
    return {"exists": exists, "path": normalized_path}

@app.get("/check-file")
def check_file(folder: str, filename: str):
    full_path = os.path.normpath(os.path.join(folder, filename))
    exists = os.path.exists(full_path) and os.path.isfile(full_path)
    return {"exists": exists, "path": full_path}

def _find_bartend_executable() -> Optional[str]:
    """Tìm đường dẫn tệp thực thi BarTender (bartend.exe) trên máy trạm Windows."""
    # 1. Kiểm tra Windows Registry App Paths
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\bartend.exe") as key:
            val, _ = winreg.QueryValueEx(key, "")
            if val and os.path.isfile(val):
                return str(val)
    except Exception:
        pass

    # 2. Kiểm tra các thư mục cài đặt tiêu chuẩn của Seagull BarTender
    candidates = [
        r"C:\Program Files\Seagull\BarTender Suite\bartend.exe",
        r"C:\Program Files (x86)\Seagull\BarTender Suite\bartend.exe",
        r"C:\Program Files\Seagull\BarTender 2016\bartend.exe",
        r"C:\Program Files (x86)\Seagull\BarTender 2016\bartend.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c

    import shutil
    return shutil.which("bartend.exe") or shutil.which("bartend")

@app.post("/open-template")
def open_template(req: OpenTemplateRequest):
    """Mở file mẫu tem .btw trực tiếp trên máy tính trạm qua BarTender Designer GUI."""
    folder = req.folder or "D:\\PAT\\Templates"
    filename = req.filename.strip() if req.filename else ""
    if not filename:
        raise HTTPException(status_code=400, detail="Filename must be provided")

    full_path = os.path.normpath(os.path.join(folder, filename))
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return {
            "success": False,
            "exists": False,
            "message": f"Tệp mẫu tem '{filename}' không tồn tại trong thư mục '{folder}'",
            "path": full_path,
            "folder": folder,
            "filename": filename,
        }

    try:
        bartend_exe = _find_bartend_executable()
        if bartend_exe and os.path.isfile(bartend_exe):
            logger.info(f"Opening template with BarTender Designer: {bartend_exe} /F={full_path} /MAX")
            subprocess.Popen([bartend_exe, f"/F={full_path}", "/MAX"])
        elif hasattr(os, "startfile"):
            logger.info(f"Opening template with os.startfile fallback: {full_path}")
            os.startfile(full_path)
        else:
            logger.info(f"[DEV MOCK] Simulated open template for '{full_path}'")
        return {
            "success": True,
            "exists": True,
            "message": f"Đã mở tệp '{filename}'",
            "path": full_path,
            "folder": folder,
            "filename": filename,
        }
    except Exception as e:
        logger.error(f"Lỗi khi mở tệp {full_path}: {e}")
        return {
            "success": False,
            "exists": True,
            "message": f"Không thể mở tệp: {str(e)}",
            "path": full_path,
            "folder": folder,
            "filename": filename,
        }

@app.post("/open-dir")
def open_directory(req: OpenDirRequest):
    """Mở thư mục trên máy tính trạm qua Windows File Explorer."""
    folder = req.folder or "D:\\PAT\\Templates"
    folder = os.path.normpath(folder)

    try:
        os.makedirs(folder, exist_ok=True)
        if hasattr(os, "startfile"):
            os.startfile(folder)
        else:
            logger.info(f"[DEV MOCK] Simulated os.startfile('{folder}')")
        return {
            "success": True,
            "message": f"Đã mở thư mục '{folder}'",
            "path": folder,
        }
    except Exception as e:
        logger.error(f"Lỗi khi mở thư mục {folder}: {e}")
        return {
            "success": False,
            "message": f"Không thể mở thư mục: {str(e)}",
            "path": folder,
        }

# === Scale Endpoints ===

@app.get("/scale/status")
def get_scale_status():
    """Lấy trạng thái kết nối cổng COM cân điện tử"""
    return scale_manager.get_status()

@app.get("/scale/ports")
def get_scale_ports():
    """Lấy danh sách cổng COM có thể kết nối cân"""
    status = scale_manager.get_status()
    return {"ports": status.get("available_ports", [])}

@app.get("/scale/current")
def get_scale_current():
    """Lấy trọng lượng và cờ ổn định thời gian thực từ cân"""
    return scale_manager.get_current_reading()

@app.post("/scale/tare")
def trigger_scale_tare():
    """Gửi lệnh trừ bì tới cân"""
    success = scale_manager.tare()
    return {"success": success}

@app.post("/scale/zero")
def trigger_scale_zero():
    """Gửi lệnh zero tới cân"""
    success = scale_manager.zero()
    return {"success": success}

@app.post("/scale/config")
def update_scale_config(cfg: ScaleConfigRequest):
    """Cập nhật cấu hình cổng COM, baudrate, và hotkey của cân"""
    port_changed = False
    if cfg.port and cfg.port != scale_manager._port:
        scale_manager._port = cfg.port
        port_changed = True
    if cfg.baudrate and cfg.baudrate != scale_manager._baudrate:
        scale_manager._baudrate = cfg.baudrate
        port_changed = True
    if cfg.hotkey:
        scale_manager._hotkey = cfg.hotkey
    if cfg.auto_connect is not None:
        scale_manager._auto_connect = cfg.auto_connect
    
    scale_manager.save_config()
    current_status = scale_manager.get_status()
    # Reconnect if port/baudrate changed OR if currently disconnected/not streaming
    if port_changed or not current_status.get("connected"):
        scale_manager.reconnect()
    return {"success": True, "config": scale_manager.get_status()}

@app.post("/scale/reconnect")
def reconnect_scale():
    """Chủ động kết nối lại cổng COM cân điện tử"""
    scale_manager.reconnect()
    return {"success": True, "config": scale_manager.get_status()}


@app.post("/print")
async def process_print(req: PrintRequest):
    try:
        content = req.xml_content
        
        result = await run_in_threadpool(
            bt_com_app.print_xml,
            xml_content=content, 
            printer_name_override=req.printer_name,
            local_template_dir=req.local_template_dir
        )
        
        if result["success"]:
            return {
                "success": True, 
                "message": result.get("message", "Print job processed via COM"),
                "type": result.get("type"),
                "data": result.get("data")
            }
        else:
            logger.error("Print job failed: %s", result.get("message", "Print failure"))
            raise HTTPException(status_code=500, detail={"code": "PRINT_FAILED"})
        
    except HTTPException: raise
    except Exception as e:
        logger.error(f"Print agent error: {e}")
        raise HTTPException(status_code=500, detail={"code": "AGENT_UNEXPECTED"})

if __name__ == "__main__":
    import uvicorn
    import argparse
    import sys
    
    # Determine execution directory (handles both python running and compiled .exe)
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))
        
    config_path = os.path.join(application_path, "config.json")
    
    default_port = 8080
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                if "port" in config_data:
                    default_port = int(config_data["port"])
        except Exception as e:
            logger.warning(f"Failed to read config.json: {e}")
    else:
        # Auto-generate default config.json
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump({"port": 8080}, f, indent=2)
            logger.info(f"Auto-generated default {config_path}")
        except Exception as e:
            logger.warning(f"Failed to auto-generate config.json: {e}")
    
    parser = argparse.ArgumentParser(description="NY Print Agent")
    parser.add_argument("--port", type=int, default=default_port, help=f"Port to run the agent on (default: {default_port})")
    args = parser.parse_args()
    
    logger.info(f"Starting Print Agent on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port)
