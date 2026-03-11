FROM python:3.12-slim

WORKDIR /app

# Install git for cloning PageIndex open-source repo
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone open-source PageIndex repo (self-hosted, no API key needed)
RUN git clone https://github.com/VectifyAI/PageIndex.git /pageindex_src

# Install app dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install PageIndex open-source dependencies
RUN pip install -r /pageindex_src/requirements.txt

# Make PageIndex importable
ENV PYTHONPATH="/pageindex_src:${PYTHONPATH}"

COPY . .

CMD [ "python", "my_agents/main.py" ]
