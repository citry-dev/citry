# Immutable public base images keep the language runtimes stable between runs.
FROM node:22-bookworm-slim@sha256:83f487e0a63425e5b4d146fb5e5be574bcbe1b7b843d3ebafdd95eaf7767a7e5 AS node
FROM python:3.12-slim-bookworm@sha256:782412e85d0f0984994c290652577d4018aff08145c85b262bb63dc0c7522254

ENV DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/opt/playwright \
    HOME=/home/agent \
    CODEX_HOME=/home/agent/.codex

COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
    && apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git ripgrep \
    && rm -rf /var/lib/apt/lists/* \
    && npm install --global @openai/codex@0.153.4 \
    && npm cache clean --force

# The context is this directory; only public package pins and this helper enter it.
COPY requirements.lock /opt/agent-eval/requirements.lock
RUN python -m pip install --no-cache-dir -r /opt/agent-eval/requirements.lock \
    && python -m pip check \
    && python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip freeze > /opt/agent-eval/requirements.freeze.txt

COPY record_versions.py /opt/agent-eval/record_versions.py
RUN groupadd --gid 1000 agent \
    && useradd --uid 1000 --gid 1000 --no-create-home --shell /bin/bash agent \
    && mkdir -p /workspace /home/agent/.codex \
    && python /opt/agent-eval/record_versions.py \
    && chown -R agent:agent /workspace /home/agent \
    && chmod -R a+rX /opt/playwright

# Each run mounts its own workspace and authentication volume at runtime.
USER agent
WORKDIR /workspace
CMD ["sleep", "infinity"]
