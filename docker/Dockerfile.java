# Alpine-based Java execution environment
FROM openjdk:17-jdk-alpine

# Install additional dependencies if needed
RUN apk add --no-cache \
    bash

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
