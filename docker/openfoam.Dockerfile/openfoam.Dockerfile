# Solver image: OpenFOAM v12 + the flowtest package.
FROM openfoam/openfoam12-paraview510

USER root
RUN apt-get update && apt-get install -y python3-pip && rm -rf /var/lib/apt/lists/*
COPY . /opt/flowtest-automation
RUN pip install --break-system-packages /opt/flowtest-automation
USER openfoam
