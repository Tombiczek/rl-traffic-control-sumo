FROM --platform=linux/amd64 ghcr.io/eclipse-sumo/sumo:v1_25_0

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV SUMO_HOME=/usr/share/sumo

RUN apt-get update \
    && apt-get install -y \
        python3 \
        python3-pip \
        python3-venv \
        xvfb \
        ffmpeg \
        x11-utils \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

RUN pip install --upgrade pip \
    && pip install \
        "pyyaml>=6.0,<7.0" \
        "stable-baselines3>=2.3,<3.0" \
        "huggingface_hub>=0.30,<1.0" \
        "PyVirtualDisplay>=3.0,<4.0" \
        "imageio>=2.34,<3.0" \
        "imageio-ffmpeg>=0.5,<1.0" \
        "Pillow>=10.0,<12.0" \
    && git clone https://github.com/LucasAlegre/sumo-rl \
    && cd sumo-rl \
    && pip install -e .

WORKDIR /workspace
COPY . /workspace

ENV PYTHONPATH=/workspace
ENV LIBSUMO_AS_TRACI=0

ENTRYPOINT ["python", "-m", "src.dqn.entrypoint"]