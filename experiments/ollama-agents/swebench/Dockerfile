FROM python:3.13-slim
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
ARG CUBIE_WHEEL=dist/qb_cubie-0.0.3-py3-none-any.whl
COPY ${CUBIE_WHEEL} /wheels/
RUN pip install --no-cache-dir /wheels/*.whl
COPY repair-config.json /adapter/config.json
WORKDIR /adapter
CMD ["python", "-c", "from ollama_agents.developer.process import main; raise SystemExit(main('/adapter/config.json'))"]
