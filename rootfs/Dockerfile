ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    bash \
    jq

# Copy rootfs
COPY rootfs /

# Install Python dependencies
RUN pip3 install --no-cache-dir -r /opt/zoho-calendar/requirements.txt

# Set working directory
WORKDIR /opt/zoho-calendar

# Make run script executable
RUN chmod a+x /opt/zoho-calendar/run.sh \
    && chmod a+x /etc/services.d/zoho-calendar/run

CMD ["/init"]
