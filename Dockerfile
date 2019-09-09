FROM amazonlinux:latest
LABEL maintainer="work@unnakim.info"

ENV PATH ~/.local/bin:$PATH

# install tools & deps.
RUN yum install -y tar gcc git cmake make wget unzip xz openssl yum-utils \
  && yum-builddep -y python3

# install NVM
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.34.0/install.sh | bash \
  && . ~/.nvm/nvm.sh \
  && nvm install stable

# install git-edge-master ffmpeg
RUN wget -O /tmp/ffmpeg-master.tar.xz https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-i686-static.tar.xz
RUN  mkdir /usr/local/ffmpeg  \
  && tar -xf /tmp/ffmpeg-master.tar.xz --directory /usr/local/ffmpeg \ 
  && export FFMPEG_FOLDER=$(find /usr/local/ffmpeg -type d -name ffmpeg-*) \
  && cp -r $FFMPEG_FOLDER/* /usr/local/ffmpeg && rm -r $FFMPEG_FOLDER \ 
  && ln -s /usr/local/ffmpeg/ffmpeg /bin/ffmpeg

# install python
RUN wget -O /tmp/python.tar.xz https://www.python.org/ftp/python/3.7.4/Python-3.7.4.tar.xz
RUN mkdir /tmp/python \
  && tar -xf /tmp/python.tar.xz --directory /tmp/python \
  && export PYTHON_FOLDER=$(find /tmp/python -type d -name Python-*) \
  && cd $PYTHON_FOLDER \
  && ./configure --with-pydebug \
  && make -s -j2 \ 
  && rm -r $PYTHON_FOLDER

# install aws-cli
RUN pip3 install awscli --upgrade --user

CMD ["/bin/bash"]