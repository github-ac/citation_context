FROM ubuntu:18.04

RUN apt-get update && apt-get install -y \
        apt-transport-https \
        build-essential \
        nano \
        cmake \
        curl \
        default-jre \
        make \
        gcc \
        git \
        software-properties-common \
        wget \
        zip \
        unzip \
        python3 \
        python3-dev \
        python-pip \
        python-virtualenv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /root
RUN pip install --upgrade pip
RUN virtualenv venv --python $(which python3.6)
COPY requirements.txt requirements.txt
RUN bash -c "source venv/bin/activate && pip install -r requirements.txt"
RUN bash -c "python -m spacy download en_core_web_sm"

RUN wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add - \
    && echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-7.x.list \
    && apt-get update && apt-get install -y elasticsearch
