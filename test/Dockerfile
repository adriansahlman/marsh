ARG PYTHON_VERSION=3.8
FROM python:${PYTHON_VERSION}

# Add Tini
ENV TINI_VERSION v0.19.0
ADD https://github.com/krallin/tini/releases/download/${TINI_VERSION}/tini /tini
RUN chmod +x /tini

ENTRYPOINT ["/tini", "--"]

VOLUME /marsh
WORKDIR /marsh

CMD ["pytest"]
