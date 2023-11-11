FROM python:3.11

WORKDIR /Team38backend

COPY requirements.txt /Team38backend

RUN pip3 install --upgrade pip -r requirements.txt

COPY . /Team38backend

ENTRYPOINT ["python3"]

CMD ["main.py"]

EXPOSE 5000