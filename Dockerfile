FROM python:3.8.10-slim as base

RUN apt-get update && \
    apt-get install -y libpoppler-qt5-1 cmake wget curl \
    && apt-get install -y software-properties-common \
    && add-apt-repository https://archive.ubuntu.com/ \
    && apt-get install -y ghostscript libmagickwand-dev \
    && rm -rf /var/lib/apt/lists/*

ARG imagemagic_config=/etc/ImageMagick-6/policy.xml
RUN if [ -f $imagemagic_config ] ; then sed -i \
    's/<policy domain="coder" rights="none" pattern="PDF" \/>/<policy domain="coder" rights="read|write" pattern="PDF" \/>/g'\
     $imagemagic_config ; else echo did not see file $imagemagic_config ; fi

WORKDIR /inference
COPY poetry.lock pyproject.toml /inference/

RUN pip install poetry
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-dev

COPY app/ app/

FROM base as build

CMD python3 -m app.main

FROM base as test

COPY tests tests
RUN pip install poetry
RUN poetry install
RUN black --check app/ && echo "black passed" \
    && isort --check app/ && echo "isort passed" \
    && pylint app/ && echo "pylint passed" \
    && mypy app/ && echo "mypy passed"
