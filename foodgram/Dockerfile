FROM python:3.8.6-slim
WORKDIR /app
COPY ./foodgram/requirements.txt .
RUN apt update && \
    apt upgrade -y && \
    python3 -m pip install --upgrade pip && \
    pip install -r requirements.txt
COPY . ./
RUN chmod +x init.sh
# CMD gunicorn foodgram.wsgi:application --bind 0.0.0.0:8000
CMD /app/init.sh