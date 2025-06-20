FROM ubuntu:latest
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y gcc python3 python3-pip build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN mkdir -p /sandbox && \
    useradd -ms /bin/bash sandboxuser && \
    chown -R sandboxuser:sandboxuser /sandbox && \
    chmod 777 /sandbox

VOLUME [ "/sandbox" ]
WORKDIR /sandbox

USER sandboxuser
CMD [ "bash" ]
