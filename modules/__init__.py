# Modules - lazy load to avoid reportlab import errors
import sys
import os

def __getattr__(name):
    from importlib import import_module
    
    core_modules = {
        "auth": "modules.auth",
        "config_loader": "modules.config_loader", 
        "crud": "modules.crud",
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
    "config_loader", 
    "crud",
    "form_engine",
    "paths",
    "sync",
    "validator",
    "omr_form_gen",
    "omr_reader", 
    "omr_bridge",
]