from flask import Flask, render_template, request, redirect, url_for
import redis
import os
import socket
import json
import random

app = Flask(__name__)

# Kitten data - in a real app, this might come from a database
KITTENS = [
    {"id": 1, "name": "Whiskers", "image": "kitten1.jpg", "description": "A playful tabby kitten"},
    {"id": 2, "name": "Snowball", "image": "kitten2.jpg", "description": "A fluffy white kitten"},
    {"id": 3, "name": "Midnight", "image": "kitten3.jpg", "description": "A sleek black kitten"},
    {"id": 4, "name": "Ginger", "image": "kitten4.jpg", "description": "An orange striped kitten"},
    {"id": 5, "name": "Patches", "image": "kitten5.jpg", "description": "A calico kitten with patches"},
    {"id": 6, "name": "Blue", "image": "kitten6.jpg", "description": "A curious kitten with blue eyes"}
]

# Initialize cache connection - will be None if Redis is unavailable
cache = None
redis_available = False
redis_host = os.environ.get('REDIS_HOST', 'localhost')
redis_port = int(os.environ.get('REDIS_PORT', 6379))

try:
    cache = redis.Redis(host=redis_host, port=redis_port, socket_connect_timeout=2)
    # Test the connection
    cache.ping()
    redis_available = True
    print("✅ Connected to Redis successfully!")
    
    # Initialize counter if it doesn't exist
    if not cache.exists('visits'):
        cache.set('visits', 0)
        
    # Initialize kitten votes if they don't exist
    for kitten in KITTENS:
        key = f"kitten:{kitten['id']}:votes"
        if not cache.exists(key):
            cache.set(key, 0)
except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError):
    print("⚠️ Redis not available. Voting functionality will be disabled.")

@app.route('/')
def index():
    """Home page showing all kittens and vote counts"""
    kitten_data = []
    visit_count = 0
    
    if redis_available:
        # Get visit count from Redis
        visit_count = int(cache.incr('visits'))
        
        # Get vote counts for each kitten
        for kitten in KITTENS:
            key = f"kitten:{kitten['id']}:votes"
            votes = int(cache.get(key))
            
            kitten_with_votes = kitten.copy()
            kitten_with_votes['votes'] = votes
            kitten_data.append(kitten_with_votes)
            
        # Sort by votes (highest first)
        kitten_data.sort(key=lambda x: x['votes'], reverse=True)
    else:
        # Without Redis, just provide kittens with zero votes
        for kitten in KITTENS:
            kitten_with_votes = kitten.copy()
            kitten_with_votes['votes'] = 0
            kitten_data.append(kitten_with_votes)
    
    return render_template('index.html', 
                          kittens=kitten_data, 
                          visit_count=visit_count,
                          hostname=socket.gethostname(),
                          redis_available=redis_available)

@app.route('/vote/<int:kitten_id>', methods=['POST'])
def vote(kitten_id):
    """Endpoint to vote for a kitten"""
    if redis_available:
        key = f"kitten:{kitten_id}:votes"
        cache.incr(key)
    return redirect(url_for('index'))

@app.route('/reset', methods=['POST'])
def reset():
    """Reset all votes"""
    if redis_available:
        for kitten in KITTENS:
            key = f"kitten:{kitten['id']}:votes"
            cache.set(key, 0)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)