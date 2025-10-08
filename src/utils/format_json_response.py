

def format_json(obj: any):
    return obj.model_dump(mode="json", exclude_none=True)