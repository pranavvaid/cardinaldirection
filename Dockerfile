FROM python:3
ADD fetchcourses.py /
RUN pip install requests
RUN pip install xmltodict
CMD [ "python", "./fetchcourses.py"]


