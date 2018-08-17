FROM python:3
LABEL Maintainer "CanDIG Project"

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt && \
    python setup.py install

EXPOSE 3000

# Run the model service server
# provide some explicit defaults if no arugments are given
ENTRYPOINT [ "python_model_service", "--port", "3000"]
CMD [ "--logfile", "model_service.log",\
      "--database", "model_service.sqlite" ]
