def deadline(project):
    if project == "Atlas":
        return 45
    if project == "Boreal":
        return 120
    raise KeyError(project)
