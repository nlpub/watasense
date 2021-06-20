FROM python:3.8-slim

MAINTAINER Dmitry Ustalov <dmitry.ustalov@gmail.com>

EXPOSE 5000

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN \
apt-get update && \
apt-get install --no-install-recommends -y -o Dpkg::Options::="--force-confold" tini curl build-essential && \
apt-get clean && \
rm -rf /var/lib/apt/lists/* && \
pip install --no-cache-dir -r requirements.txt

RUN \
curl -sL https://download.cdn.yandex.net/mystem/mystem-3.0-linux3.1-64bit.tar.gz | tar zx mystem && \
mv mystem /bin && \
chmod +x /bin/mystem

COPY . .

RUN ./mnogoznal_web_assets.py

USER nobody

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["uwsgi", "--http", "0.0.0.0:5000", "--master", "--module", "mnogoznal_web:app", "--processes", "4", "--threads", "1", "--harakiri", "30"]
