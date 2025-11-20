FROM public.ecr.aws/docker/library/python:3.14-slim
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter
ENV PORT=8000
WORKDIR /var/task
COPY requirements.txt ./
# Herramientas de compilación necesarias para dependencias que usan C/C++
RUN apt-get update \
	&& apt-get install -y --no-install-recommends g++ cmake ninja-build\
	&& rm -rf /var/lib/apt/lists/* \
    && python -m pip install --upgrade pip setuptools wheel \
	&& pip install --verbose -r requirements.txt
COPY ./app ./
CMD exec uvicorn --port=$PORT main:app