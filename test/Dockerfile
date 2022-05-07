ARG PYTHON_VERSION=3.8
FROM python:${PYTHON_VERSION}

COPY requirements.txt ./
COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt
RUN rm requirements.txt requirements-dev.txt

VOLUME /marsh
WORKDIR /marsh

ENV PATH /marsh:$PATH
ENV PYTHONPATH /marsh:$PYTHONPATH

# Add Tini
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

ENTRYPOINT ["/tini", "--"]

CMD ["pytest"]
