FROM python:3
ADD collectcourses.py /
ADD stanfordclasses.py /
ADD cardinaldirection.py /
ADD stanfordclasslist.pkl /
RUN mkdir /pickles
RUN pip install requests
RUN pip install xmltodict
CMD [ "python", "./cardinaldirection.py"]
#CMD [ "python", "./collectcourses.py"]

