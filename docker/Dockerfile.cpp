# Alpine-based C++ execution environment
FROM alpine:3.18

# Install C++ compiler and runtime dependencies
RUN apk add --no-cache \
    g++ \
    gcc \
    musl-dev \
    libc-dev \
    make \
    libstdc++

# Create a non-root user for security
RUN adduser -D -u 1000 coderunner

# Create workspace directory
RUN mkdir -p /workspace && \
    chown coderunner:coderunner /workspace

# Set working directory
WORKDIR /workspace

# Switch to non-root user
USER coderunner

# Set default command
CMD ["/bin/sh"]
