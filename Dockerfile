FROM ubuntu:latest
LABEL authors="Meirmanov"

ENTRYPOINT ["top", "-b"]