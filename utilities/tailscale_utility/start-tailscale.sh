#!/bin/bash

# Authenticate Tailscale (you'd need a method to provide the auth key, perhaps through an environment variable or another mechanism)
tailscale up --authkey=tskey-auth-kXzqY92CNTRL-dQS32nvRc9YTS1mBYsgwGYzDwAnfLRE7

# Set up routing (this is a basic example and might need adjustments)
iptables -t nat -A POSTROUTING -o tailscale0 -j MASQUERADE

# Keep the container running
tailscale status --listen localhost:41112
