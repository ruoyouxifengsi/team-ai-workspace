FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

COPY pyproject.toml ./

# Default: PyPI. Mainland China users: swap to Tsinghua mirror to avoid
# the 90-second timeout building cryptography / openpyxl / pypdf wheels.
# RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -e .
RUN pip install --no-cache-dir -e .

COPY app/ ./app/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
