#!/usr/bin/env python3
# -*- coding: utf-8 -*-
user = None
system = None
nullAI = None

def load_ai_engine(engine_name: str):
    """Load and bind the correct AI engine based on the given name."""
    global user, system, nullAI
    engine_name = engine_name.lower()

    if engine_name == "xai":
        from xai_sdk.chat import user as xai_user, system as xai_system
        user = xai_user
        system = xai_system
        nullAI = None

    elif engine_name == "nullai":
        from nullAI import user as null_user, system as null_system, nullAI as _NullAI
        nullAI = _NullAI
        user = null_user
        system = null_system

    else:
        raise ValueError(f"Unknown AI engine: {engine_name}")
