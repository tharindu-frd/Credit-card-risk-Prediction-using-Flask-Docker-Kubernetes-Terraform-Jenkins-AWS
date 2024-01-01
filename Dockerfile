FROM ubuntu
RUN apt  update
RUN apt install -y python3 python3-pip 
RUN pip3 install flask

RUN mkdir app
WORKDIR /app
COPY . /app/
RUN pip install  -r requirements.txt
EXPOSE 5000

CMD ["python3","app.py"]


