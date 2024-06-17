FROM quay.io/jupyter/minimal-notebook

USER root

RUN apt update
RUN apt install -y graphviz
RUN apt install -y wget

RUN python -m pip install --upgrade pip
RUN python -m pip install naturf

RUN wget https://raw.githubusercontent.com/IMMM-SFA/naturf/main/notebooks/quickstarter.ipynb

RUN rm -rf work
