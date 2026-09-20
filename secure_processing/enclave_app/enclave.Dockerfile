# Dockerfile for building CareerVerse AI AWS Nitro Enclave Image (EIF)
# Base image minimal Python on Amazon Linux 2023
FROM public.ecr.aws/amazonlinux/amazonlinux:2023-minimal

# Install Python 3.11 and cryptographic libraries
RUN dnf install -y python3.11 python3.11-pip shadow-utils && \
    dnf clean all

# Create non-root enclave user
RUN useradd -u 1001 -m -s /sbin/nologin enclaveuser

WORKDIR /app

# Install minimal required dependencies for inside the enclave
COPY requirements_enclave.txt .
RUN pip3.11 install --no-cache-dir -r requirements_enclave.txt

# Copy enclave application and core secure engines
COPY secure_processing/ /app/secure_processing/
COPY secure_processing/enclave_app/enclave_server.py /app/

# Switch to non-root user
USER enclaveuser

# Enclave communicates strictly through AF_VSOCK (no external network interfaces)
CMD ["python3.11", "/app/enclave_server.py"]
