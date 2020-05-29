FROM python:3.6

RUN mkdir -p usr/src/dinasore-ua

WORKDIR /usr/src/dinasore-ua

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY communication ./communication
COPY opc_ua ./opc_ua
COPY core ./core
COPY data_model ./data_model
COPY tests ./tests
COPY resources ./resources
# RUN python tests/__init__.py

ENTRYPOINT [ "python", "core/main.py", "-a", "0.0.0.0"]
