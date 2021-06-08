FROM docker.dbc.dk/dbc-python3:latest
RUN useradd -m python
RUN apt update
RUN pip install requests
WORKDIR /home/python
COPY --chown=python scripts scripts
