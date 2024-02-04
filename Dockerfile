FROM python:3.12-slim

RUN apt-get update -qq \
    && apt-get install --yes -qq \
    build-essential \
    curl \
    git \
    libfl-dev \
    lighttpd \
    procps \
    unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/latin-macronizer

# Build morpheus.
RUN git clone --depth=1 https://github.com/Alatius/morpheus.git
RUN cd morpheus/src \
    && make \
    && make install \
    && cd .. \
    && ./update.sh \
    && ./update.sh 

# Install RFTagger.
RUN curl -sSL -o RFTagger.zip https://www.cis.uni-muenchen.de/~schmid/tools/RFTagger/data/RFTagger.zip \
    && echo '598f467a37ed3722aa547d12f13877c242197cefcec7edc004b8c1713b3ab3ed  RFTagger.zip' \
    | sha256sum -c - \
    && unzip RFTagger.zip \
    && rm RFTagger.zip \
    && cd RFTagger/src \
    && make \
    && make install \
    && cd ../.. \
    && rm -rf ./RFTagger

# Copy project files.
COPY *.txt *.py *.sh ./

# Initialize data.
RUN git clone --depth=1 https://github.com/Alatius/treebank_data.git \
    && ./train-rftagger.sh \
    && python macronize.py --initialize \
    && rm -rf ./treebank_data

# Configure web server.
# Adjust the CGI module config and enable.
RUN sed -i \
    -e '/cgi.assign/s "" ".py" ' \
    -e '/cgi.assign/s "" "/usr/local/bin/python" ' \
    /etc/lighttpd/conf-available/10-cgi.conf \
    && lighty-enable-mod cgi \
    && ln -s /opt/latin-macronizer/macronize.py /usr/lib/cgi-bin/macronize.py

CMD /bin/bash
