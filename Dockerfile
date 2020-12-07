FROM python:slim

RUN mkdir /app
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
ENTRYPOINT [ "/app/register.py" ]
