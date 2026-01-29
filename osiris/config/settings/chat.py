import os


CHAT_ATTACHMENT_MAX_SIZE = int(os.getenv("CHAT_ATTACHMENT_MAX_SIZE", 25 * 1024 * 1024))
CHAT_ALLOWED_CONTENT_TYPES = tuple(
    t
    for t in os.getenv(
        "CHAT_ALLOWED_CONTENT_TYPES",
        ",".join(
            [
                "image/jpeg",
                "image/png",
                "image/gif",
                "image/webp",
                "application/pdf",
                "text/plain",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ]
        ),
    ).split(",")
    if t
)
CHAT_FORBIDDEN_EXTENSIONS = tuple(
    ext
    for ext in os.getenv(
        "CHAT_FORBIDDEN_EXTENSIONS",
        ".exe,.bat,.cmd,.com,.msi,.js,.vbs,.ps1,.sh",
    ).split(",")
    if ext
)
CHAT_POLLING_INTERVAL_SECONDS = int(os.getenv("CHAT_POLLING_INTERVAL_SECONDS", "8"))
