FROM sofaframework/sofabuilder_ubuntu:latest

ENV MYVARIABLE=0

RUN apt update
RUN apt install -y wget unzip git locales locales-all sqlite3
RUN locale-gen en_US.UTF-8
RUN update-locale LANG=en_US.UTF-8
RUN wget https://github.com/sofa-framework/sofa/releases/download/v24.06.00/SOFA_v24.06.00_Linux.zip
RUN unzip SOFA_v24.06.00_Linux.zip
RUN python3.10 -m pip install pathlib numpy plotly
RUN python3.10 -m pip install gmsh==4.11.1 optuna==2.10.0 SQLALchemy==1.4.44 matplotlib
RUN git clone https://github.com/Ignaciojc1/SoftRobots.DesignOptimization.git /home/ci/SoftRobots.DesignOptimization

ENV PATH="/builds/SOFA_v24.06.00_Linux/bin:$PATH"
ENV PYTHONPATH="/builds/SOFA_v24.06.00_Linux/plugins/SofaPython3/lib/python3/site-packages/"
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en.US.UTF-8