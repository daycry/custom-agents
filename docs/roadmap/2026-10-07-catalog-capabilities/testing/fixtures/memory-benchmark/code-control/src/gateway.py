from .policy import deadline
from .storage import append

def accept(request):
    limit = deadline(request.project)
    return append(request, limit)
