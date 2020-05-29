FROM amazonlinux:latest
LABEL maintainer="work@unnakim.info"

ENV PATH ~/.local/bin:$PATH

ENV PYTHON_VERSION 3.7.4
ENV NVM_VERSION 0.34.0

ENV NVM_SCRIPT_URL https://raw.githubusercontent.com/nvm-sh/nvm/v${NVM_VERSION}/install.sh
ENV FFMPEG_URL https://johnvansickle.com/ffmpeg/builds/ffmpeg-git-amd64-static.tar.xz
ENV PYTHON_URL https://www.python.org/ftp/python/${PYTHON_VERSION}/Python-${PYTHON_VERSION}.tar.xz

# install tools & deps.
RUN yum install -y tar gcc git cmake make wget unzip xz openssl yum-utils \
  && yum-builddep -y python3

# install NVM
RUN curl -o- $NVM_SCRIPT_URL | bash \
  && . ~/.nvm/nvm.sh \
  && nvm install stable

# install git-edge-master ffmpeg
RUN wget -O /tmp/ffmpeg-master.tar.xz $FFMPEG_URL
RUN  mkdir /usr/local/ffmpeg  \
  && tar -xf /tmp/ffmpeg-master.tar.xz --directory /usr/local/ffmpeg \ 
  && export FFMPEG_FOLDER=$(find /usr/local/ffmpeg -type d -name ffmpeg-*) \
  && cp -r $FFMPEG_FOLDER/* /usr/local/ffmpeg && rm -r $FFMPEG_FOLDER \ 
  && ln -s /usr/local/ffmpeg/ffmpeg /bin/ffmpeg

# build python
RUN wget -O /tmp/python.tar.xz $PYTHON_URL
RUN mkdir /tmp/python \
  && tar -xf /tmp/python.tar.xz --directory /tmp/python \
  && export PYTHON_FOLDER=$(find /tmp/python -type d -name Python-*) \
  && cd $PYTHON_FOLDER \
  && ./configure --with-pydebug \
  && make -s -j2 \ 
  && rm -r $PYTHON_FOLDER

# install aws-cli
RUN pip3 install awscli --upgrade --user

COPY scripts/* /runtime/scripts/

CMD ["/bin/bash"]
