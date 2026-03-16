def get_ip_from_request(request) -> str:
    """Extract client IP address from request"""
    if request:
        forwarded = request.headers.get("x-forwarded-for")

        if not request.client:
            return None

        if forwarded:
            client_ip = forwarded.split(",")[0]
        else:
            client_ip = request.client.host

    return client_ip