FROM python:3.13-slim

ARG USER=django
ARG WORKDIR=/django_backend
ARG POETRY_VERSION=2.1.2

RUN pip install -U pip \
    && apt-get update

# Install required system packages
COPY docker/non-production/packages.txt .

RUN xargs apt -y install < packages.txt \
    && rm -rf /var/lib/apt/lists/*

WORKDIR ${WORKDIR}

RUN useradd -ms /bin/bash ${USER} && \
    usermod -aG root ${USER} && \
    chown -R ${USER}:${USER} ${WORKDIR} && \
    chmod -R 755 ${WORKDIR}

RUN chmod -R g+w /usr/local/

USER ${USER}

# Install and setup poetry
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_HOME="/home/${USER}/.poetry"

RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/home/${USER}/.poetry/bin:${PATH}"

RUN poetry completions bash >> ~/.bash_completion
RUN poetry config virtualenvs.create false

# Copy required poetry files
COPY pyproject.toml .
COPY poetry.lock .

# Install the dependencies
RUN poetry install  --no-root --no-interaction --no-ansi
