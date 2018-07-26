FROM python:3

COPY . /app
WORKDIR /app

RUN pip install -r reqirements.txt && \
    python setup.py install

CMD [ "python", "./my_script.py" ]
