# Use a base image with a lightweight Linux distribution
FROM ubuntu:latest

# Install necessary tools and Tailscale
RUN apt update && apt install -y curl iproute2 iptables && \
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.gpg | apt-key add - && \
    curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/focal.list | tee /etc/apt/sources.list.d/tailscale.list && \
    apt update && apt install -y tailscale

# Expose the necessary ports (this can be adjusted based on your requirements)
# For instance, Tailscale's default ports are UDP 41641 and others as needed.
EXPOSE 41641/udp

# Set up a script to handle Tailscale authentication and service start-up
COPY start-tailscale.sh /start-tailscale.sh
RUN chmod +x /start-tailscale.sh

# Start Tailscale on container start-up
CMD ["/start-tailscale.sh"]
