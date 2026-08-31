def get_ip_from_request(request) -> str:
    """
    Extract client IP address from request.
    This is required for logging client IPs in the application, which can be useful for debugging, analytics, or security purposes.
    
    :param request: FastAPI Request object
    :return: Client IP address as string, or None if it cannot be determined
    """
    if request:
        forwarded = request.headers.get("x-forwarded-for")

        if not request.client:
            return None

        if forwarded:
            client_ip = forwarded.split(",")[0]
        else:
            client_ip = request.client.host

    return client_ip