FROM python:3.7-alpine

RUN apk  add --no-cache dumb-init # build-base

WORKDIR /src

COPY requirements.txt /src/

RUN pip install -r requirements.txt

COPY . /src/

ENTRYPOINT ["dumb-init", "--"]
CMD ["python", "-m", ""]

