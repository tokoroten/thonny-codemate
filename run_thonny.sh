#!/bin/bash
# Run Thonny with the virtual environment
export UV_LINK_MODE=copy
.venv/bin/python -m thonny "$@"
