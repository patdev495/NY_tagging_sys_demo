"""
Core Utility Functions — Unified and robust system helpers.
Encapsulates Template Path Resolution and Environment Detection.
"""
import os
import sys

from src.core.config import settings


class TemplateResolver:
    """
    Unified template resolver for BarTender BTW files.
    Acts as the Single Source of Truth for path resolution and template search strategies.
    Supports both backend server execution and client-side print agent execution.
    """
    DEFAULT_TEMPLATES_DIR = "D:\\PAT\\Templates"
    CANONICAL_TEMPLATE_MAP = {
        "erro_03": "erro_03.btw",
        "erro_02": "erro_02.btw",
        "erro_01": "erro_01.btw",
        "erro_04": "erro_04.btw",
        "erro_05": "erro_05.btw",
        "standard": "carton_base.btw",
        "detailed": "carton_detail.btw",
    }
    ALL_CANONICAL_TEMPLATES = [
        {"filename": "erro_03.btw", "customer": "ERRO", "type": "erro_03", "name": "Erro 03 (Luxshare NME PD024364)"},
        {"filename": "erro_02.btw", "customer": "ERRO", "type": "erro_02", "name": "Erro 02 (Pallet SSCC-18 & ASIN)"},
        {"filename": "erro_01.btw", "customer": "ERRO", "type": "erro_01", "name": "Erro 01 (Thùng Carton SN + Rev)"},
        {"filename": "erro_04.btw", "customer": "ERRO", "type": "erro_04", "name": "Erro 04 (PD027032 eero carton)"},
        {"filename": "erro_05.btw", "customer": "ERRO", "type": "erro_05", "name": "Erro 05 (PD016906 Pegatron NN9)"},
        {"filename": "carton_base.btw", "customer": "UI", "type": "standard", "name": "UI Tem Thùng Tiêu Chuẩn (Patch Cords)"},
        {"filename": "Carton_45.btw", "customer": "UI", "type": "standard", "name": "UI Tem Thùng Cáp 4.5M/5M/8M (BK Cables)"},
        {"filename": "carton_detail_1M_W.btw", "customer": "UI", "type": "detailed", "name": "UI Tem Chi Tiết Cáp 1M (Lưới 40 S/N)"},
        {"filename": "carton_detail_2_3M_W.btw", "customer": "UI", "type": "detailed", "name": "UI Tem Chi Tiết Cáp 2M/3M (Lưới 40 S/N)"},
        {"filename": "carton_detail_UISP_Connector_SHD.btw", "customer": "UI", "type": "detailed", "name": "UI Tem Chi Tiết UISP Connector"},
    ]

    @classmethod
    def get_canonical_template_filename(cls, template_type: str | None) -> str:
        """Return canonical BarTender template filename (.btw) for a template_type."""
        normalized_type = (template_type or "standard").strip().lower()
        return cls.CANONICAL_TEMPLATE_MAP.get(normalized_type, "carton_base.btw")

    @classmethod
    def check_template_exists(cls, template_name_or_path: str, custom_dir: str | None = None) -> dict:
        """Verify whether a template file exists in the given directory or standard directories."""
        filename = os.path.basename(template_name_or_path)
        root = cls.get_execution_root()
        search_dirs = []
        if custom_dir:
            search_dirs.append(os.path.normpath(custom_dir))
        search_dirs.extend([
            os.path.normpath(cls.DEFAULT_TEMPLATES_DIR),
            os.path.normpath(os.path.join(root, getattr(settings, 'LABEL_TEMPLATES_DIR', 'resources/templates'))),
            os.path.normpath(os.path.join(root, 'resources', 'templates')),
            os.path.normpath(root),
        ])

        for d in search_dirs:
            candidate = os.path.normpath(os.path.join(d, filename))
            if os.path.exists(candidate):
                return {"exists": True, "path": candidate, "searched_dirs": search_dirs}

        return {"exists": False, "path": None, "searched_dirs": search_dirs}

    @staticmethod
    def get_execution_root() -> str:
        """Determines the correct execution root directory, handling PyInstaller environments."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        
        # Dev mode safe root detection
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, "main.py")) or os.path.exists(os.path.join(cwd, "src")):
            return cwd
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    @classmethod
    def resolve(cls, path: str | None, fallback_path: str | None = None, local_dir: str | None = None, default_filename: str = "carton.ui.btw") -> str:
        """
        Resolves a BTW template path using structured search strategies.
        Checks local directory overrides first, then database settings, then resource fallback directories.
        """
        root = cls.get_execution_root()
        
        # Strategy 1: Prioritize local directory override if provided by client (remap)
        if local_dir and path:
            filename = os.path.basename(path)
            local_path = os.path.normpath(os.path.join(local_dir, filename))
            if os.path.exists(local_path):
                return local_path

        # Strategy 2: Check standard DEFAULT_TEMPLATES_DIR (e.g. D:\PAT\Templates)
        if path:
            filename = os.path.basename(path)
            standard_path = os.path.normpath(os.path.join(cls.DEFAULT_TEMPLATES_DIR, filename))
            if os.path.exists(standard_path):
                return standard_path
            
        def evaluate_path(p: str | None) -> str | None:
            if not p:
                return None
            
            # If absolute path, verify existence and return
            if os.path.isabs(p) or (":" in p and "\\" in p):
                norm = os.path.normpath(p)
                if os.path.exists(norm):
                    return norm
                return None
                
            # Strategy 2: Check relative to settings template directory
            templates_dir = getattr(settings, 'LABEL_TEMPLATES_DIR', 'resources/templates')
            path1 = os.path.normpath(os.path.join(root, templates_dir, p))
            if os.path.exists(path1):
                return path1
                
            # Strategy 3: Check relative to execution root directly
            path2 = os.path.normpath(os.path.join(root, p))
            if os.path.exists(path2):
                return path2
                
            return None

        # Check primary path
        resolved = evaluate_path(path)
        if resolved:
            return resolved
            
        # Check fallback path
        if fallback_path:
            resolved = evaluate_path(fallback_path)
            if resolved:
                return resolved

        # Final absolute fallback path if nothing exists (safety net)
        fallback_dir = getattr(settings, 'LABEL_TEMPLATES_DIR', 'resources/templates')
        final_path = os.path.normpath(os.path.join(root, fallback_dir, os.path.basename(path or fallback_path or default_filename)))
        return final_path


# --- Backward Compatible Thin Wrappers ---

def get_backend_root() -> str:
    """Get backend execution root directory."""
    return TemplateResolver.get_execution_root()

def resolve_template_path(primary_path: str | None = None, fallback_path: str | None = None) -> str:
    """Resolve BarTender label template path."""
    return TemplateResolver.resolve(primary_path, fallback_path)
