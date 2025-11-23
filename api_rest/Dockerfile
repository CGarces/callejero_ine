FROM public.ecr.aws/docker/library/python:3.14-slim
COPY --from=public.ecr.aws/awsguru/aws-lambda-adapter:0.9.1 /lambda-adapter /opt/extensions/lambda-adapter
ENV PORT=8000
WORKDIR /var/task
COPY requirements.txt ./
RUN pip install --verbose -r requirements.txt
COPY ./app ./
CMD exec uvicorn --port=$PORT main:app