FROM python:3
ADD collectcourses.py /
ADD stanfordclasses.py /
ADD cardinaldirection.py /
ADD stanfordclasslist.pkl /
ADD departmentstograph.txt /
ADD coursemap.py /
RUN mkdir /pickles
RUN pip install requests
RUN pip install xmltodict
RUN pip install networkx
#CMD [ "python", "./cardinaldirection.py"]
#CMD [ "python", "./collectcourses.py"]
CMD [ "python", "./coursemap.py"]