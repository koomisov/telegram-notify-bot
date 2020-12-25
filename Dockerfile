FROM python:3.6

RUN mkdir -p /usr/src/app/
WORKDIR /usr/src/app/
COPY . /usr/src/app/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

RUN chmod +x launch_bot.sh

CMD ["./launch_bot.sh"]
