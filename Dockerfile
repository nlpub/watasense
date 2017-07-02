FROM python:3-onbuild

MAINTAINER Dmitry Ustalov <dmitry.ustalov@gmail.com>

RUN \
curl -sL https://download.cdn.yandex.net/mystem/mystem-3.0-linux3.1-64bit.tar.gz | tar zx && \
mv mystem /bin

EXPOSE 5000

USER nobody

CMD ["uwsgi", "--http", "0.0.0.0:5000", "--master", "--module", "watset_wsd:app", "--processes", "4", "--threads", "1"]
