# Use the official Ubuntu image

FROM ubuntu:latest as builder


# Update and upgrade packages
# Install Python and pip
RUN apt-get update -y #&& \
    #apt-get install -o Acquire::http::Pipeline-Depth=0 -y python3 python3-pip && \
    #ln -sf /usr/bin/python3 /usr/bin/python3

# Use the official Ubuntu image

FROM ubuntu:latest


# Copy only the installed Python and Pip binaries from the builder stage
#COPY --from=builder /usr/bin/python3 /usr/bin/python3
#COPY --from=builder /usr/lib /usr/lib
#COPY --from=builder /etc/ssl /etc/ssl
#COPY --from=builder /usr/bin/python3 /usr/bin/python3
#COPY --from=builder /usr/bin/pip3 /usr/bin/pip3
COPY --from=builder / /

# Create and set the working directory
WORKDIR /2024_01_31_00_15_49_287267

# Set the entrypoint to run hello_world.py
CMD ["/bin/bash", "runScript.sh"]
