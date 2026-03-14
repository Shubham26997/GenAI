FROM python:3.12

WORKDIR /app

RUN pip install uv

RUN uv venv --python 3.12

COPY uv.lock pyproject.toml /app/

RUN uv 

COPY requirements.txt /app/

COPY . .

CMD ["python" , "--version"]