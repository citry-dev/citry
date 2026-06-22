"""
Integrations with web servers and other host infrastructure.

Citry itself cannot listen on a port; these modules mount its route table
(``Citry.urls``: cached component JS/CSS, the client runtime, extension
endpoints) into a host application:

- ``citry.contrib.asgi``: a generic ASGI sub-application; mountable in
  Starlette, FastAPI, Litestar, Quart, Django (ASGI), and anything else that
  can mount an ASGI app.
- ``citry.contrib.wsgi``: the WSGI twin, for Flask, Pyramid, Bottle, and
  classic Django WSGI.
- ``citry.contrib.fastapi``: ``mount()`` convenience for FastAPI/Starlette
  applications.

Each module imports its host packages lazily, so importing ``citry`` never
requires them. See docs/design/dependencies.md section 9.
"""
