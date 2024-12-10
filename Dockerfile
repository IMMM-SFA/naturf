# Stage 1: Build Stage
FROM ghcr.io/msd-live/jupyter/python-notebook:latest as builder

USER root

RUN apt-get update

# Set up GDAL so users on ARM64 architectures can build the Fiona wheels
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal
RUN apt-get install -y \
    build-essential \
    gdal-bin \
    libgdal-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install naturf
RUN pip install --upgrade pip
RUN pip install naturf

# Stage 2: Final Stage
FROM ghcr.io/msd-live/jupyter/python-notebook:latest

USER root

# Install graphviz
RUN apt-get update
RUN apt-get install -y graphviz

# Copy python packages installed/built from the builder stage
COPY --from=builder /opt/conda/lib/python3.11/site-packages /opt/conda/lib/python3.11/site-packages

# To test this container locally, run:
# docker build -t naturf .
# docker run --rm -p 8888:8888 naturf
