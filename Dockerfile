FROM python:3.4-alpine

COPY . /code
WORKDIR /code

RUN apk add --no-cache gcc musl-dev btrfs-progs
RUN pip install -r requirements.txt
RUN touch /btrfs-volume

VOLUME /etc/cobalt

EXPOSE 80

CMD ["sh", "entry.sh"]

