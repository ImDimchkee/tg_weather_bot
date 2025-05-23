FROM python:3.12

WORKDIR /opt/flipperd-bot

COPY bot.py open_meteo.py .env requirements /opt/flipperd-bot/

RUN pip3 install -r requirements --upgrade

CMD [ "python3", "bot.py" ]
