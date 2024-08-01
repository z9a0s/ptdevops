FROM python:3.11.9-bullseye
WORKDIR /bot
COPY . .
RUN apt update && apt install -y nano
RUN pip install -r requirements.txt
CMD ["python", "bot.py"]
