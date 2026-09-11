"""Choose a plan through a Python event handler."""

from fastapi import FastAPI

PLANS = {
    "starter": ("Starter", 12),
    "team": ("Team", 29),
    "scale": ("Scale", 79),
}

app = FastAPI()
