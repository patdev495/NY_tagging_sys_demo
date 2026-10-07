"""
Agent Utility Functions — Unified and robust system helpers.
Encapsulates Template Path Resolution and Environment Detection.
"""
import os
import sys
from typing import Optional

class TemplateResolver:
    """
    Unified template resolver for BarTender BTW files.
    Acts as the Single Source of Truth for path resolution and template search strategies.
    Specially adapted for client-side Print Agent environments.
    """
    
    @staticmethod
    def get_execution_root() -> str:
        """Determines the correct execution root directory, handling PyInstaller environments."""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        
        # Dev mode safe root detection
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, "agent.py")):
            return cwd
        return os.path.dirname(os.path.abspath(__file__))

    @classmethod
    def resolve(cls, path: Optional[str], fallback_path: Optional[str] = None, local_dir: Optional[str] = None, default_filename: str = "carton.ui.btw") -> str:
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
            
        def evaluate_path(p: str) -> Optional[str]:
            if not p:
                return None
            
            # If absolute path, verify existence and return
            if os.path.isabs(p) or (":" in p and "\\" in p):
                norm = os.path.normpath(p)
                if os.path.exists(norm):
                    return norm
                return None
                
            # Strategy 2: Check relative to standard resources/templates directory
            path1 = os.path.normpath(os.path.join(root, "resources", "templates", p))
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
        final_path = os.path.normpath(os.path.join(root, "resources", "templates", os.path.basename(path or fallback_path or default_filename)))
        return final_path
