FROM python:3.12-slim-trixie

# The installer requires curl (and certificates) to download the release archive
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

COPY *.py /
COPY *.json /
COPY uv.lock /
COPY pyproject.toml /
COPY data /data
COPY prefix_tuning /prefix_tuning
COPY scripts /scripts
COPY planninggraph /planninggraph

RUN uv sync

CMD ["uv", "run", "python", "./prefix_tuning/train_graph_models.py", "--base-model", "distilgpt2", "--examples", "./data/training_data_combined_train.json", "--val-examples", "./data/training_data_combined_val.json"]