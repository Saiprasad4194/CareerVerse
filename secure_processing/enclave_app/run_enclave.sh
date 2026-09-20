#!/usr/bin/env bash
# ==============================================================================
# CareerVerse AI - AWS Nitro Enclaves Build & Run Automation Script
# ==============================================================================
set -e

IMAGE_TAG="careerverse-enclave:latest"
EIF_FILE="careerverse-enclave.eif"
CPU_COUNT=2
MEMORY_MB=1024
ENCLAVE_CID=16

echo "================================================================="
echo "Building CareerVerse AI Confidential Enclave Image (EIF)"
echo "================================================================="

# 1. Build Docker image
docker build -t ${IMAGE_TAG} -f secure_processing/enclave_app/enclave.Dockerfile .

# 2. Build Enclave Image File (EIF) using nitro-cli
echo "Generating cryptographic measurements and EIF..."
nitro-cli build-enclave \
    --docker-uri ${IMAGE_TAG} \
    --output-file ${EIF_FILE}

# 3. Print PCR Measurements (PCR0, PCR1, PCR2)
echo "-----------------------------------------------------------------"
echo "Cryptographic Measurements (PCRs):"
nitro-cli describe-eif --eif-path ${EIF_FILE}
echo "-----------------------------------------------------------------"

# 4. Terminate any existing enclave instance
EXISTING_ENCLAVE_ID=$(nitro-cli describe-enclaves | jq -r '.[0].EnclaveID // empty')
if [ -n "$EXISTING_ENCLAVE_ID" ]; then
    echo "Stopping existing enclave $EXISTING_ENCLAVE_ID..."
    nitro-cli terminate-enclave --enclave-id "$EXISTING_ENCLAVE_ID"
fi

# 5. Launch Enclave
echo "Starting Nitro Enclave with CID=${ENCLAVE_CID}, CPUs=${CPU_COUNT}, RAM=${MEMORY_MB}MB..."
nitro-cli run-enclave \
    --eif-path ${EIF_FILE} \
    --cpu-count ${CPU_COUNT} \
    --memory ${MEMORY_MB} \
    --enclave-cid ${ENCLAVE_CID} \
    --attach-console

echo "CareerVerse AI Hardware Enclave is RUNNING and listening on AF_VSOCK (port 5000)."
