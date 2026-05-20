FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY mcp_server ./mcp_server

RUN pip install --no-cache-dir .

ENV MCP_TRANSPORT=streamable-http
ENV MCP_HOST=0.0.0.0
ENV PORT=8080

EXPOSE 8080

CMD ["python", "-m", "mcp_server.server"]
