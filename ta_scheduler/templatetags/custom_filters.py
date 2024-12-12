from django import template

register = template.Library()


@register.filter
def unique(objects):
    """
    Removes duplicates from a list of dictionaries or items.
    """
    print("DEBUG: Input to unique filter ->", objects)
    if isinstance(objects, list):
        seen = set()
        unique_list = []
        for obj in objects:
            # Use 'username' to determine uniqueness (fallback to obj itself if no attribute is found)
            identifier = getattr(obj, 'username', obj)  # Adjust the key here (e.g., 'id', 'username', etc.)
            if identifier not in seen:
                seen.add(identifier)
                unique_list.append(obj)
        print("DEBUG: Result after unique filter ->", unique_list)
        return unique_list
    return objects