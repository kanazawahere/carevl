# Modules - lazy load to avoid reportlab import errors
import sys
import os

def __getattr__(name):
    from importlib import import_module
    
    core_modules = {
        "auth": "modules.auth",
        "app_update": "modules.app_update",
        "config_loader": "modules.config_loader", 
        "crud": "modules.crud",
        "crud_phase2": "modules.crud_phase2",
        "import_service": "modules.import_service",
        "record_store": "modules.record_store",
        "form_engine": "modules.form_engine",
        "paths": "modules.paths",
        "sync": "modules.sync",
        "validator": "modules.validator",
        "omr_form_gen": "modules.omr_form_gen",
        "omr_reader": "modules.omr_reader",
        "omr_bridge": "modules.omr_bridge",
    }
    
    if name in core_modules:
        return import_module(core_modules[name])
    
    raise AttributeError(f"module has no attribute '{name}'")

__all__ = [
    "auth",
    "app_update",
    "config_loader", 
    "crud",
    "crud_phase2",
    "import_service",
    "record_store",
    "form_engine",
    "paths",
    "sync",
    "validator",
    "omr_form_gen",
    "omr_reader", 
    "omr_bridge",
]
