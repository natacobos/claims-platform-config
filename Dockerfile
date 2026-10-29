FROM python:3.12.7-slim

# kustomize: official release binary for this machine's architecture (amd64 or arm64), checksum verified.
ARG TARGETARCH
ARG KUSTOMIZE_VERSION=v5.4.3
ADD https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2F${KUSTOMIZE_VERSION}/kustomize_${KUSTOMIZE_VERSION}_linux_${TARGETARCH}.tar.gz /tmp/
ADD https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2F${KUSTOMIZE_VERSION}/checksums.txt /tmp/
RUN cd /tmp && sha256sum --check --ignore-missing checksums.txt \
    && tar -xzf kustomize_${KUSTOMIZE_VERSION}_linux_${TARGETARCH}.tar.gz -C /usr/local/bin kustomize \
    && rm /tmp/kustomize_* /tmp/checksums.txt

WORKDIR /repo
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY scripts/run.sh /usr/local/bin/run.sh
# Remove Windows line endings in case the repository was checked out with CRLF.
RUN sed -i 's/\r$//' /usr/local/bin/run.sh
ENTRYPOINT ["sh", "/usr/local/bin/run.sh"]
