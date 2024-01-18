import json
from collections import defaultdict
from copy import deepcopy
from itertools import chain
from typing import Any, Callable, Dict, Generator, List, Tuple, Union, Iterable, Optional

def to_readable_dict(input: Union[Dict, List]):
    if isinstance(input, dict):
        return json.dumps(input, indent=4)
    else:
        return input

# nested filter (filter nested dict or list)
def nfilter(collection: Union[Dict, List], condition: Callable[[Any], bool]) -> Union[Dict, List]:
    """Filters a collection (either a dictionary or a list) based on a given condition.

    This static method delegates to either `filter_dict` or `filter_list` based on the
    type of the collection.

    Args:
        collection: A collection to filter, either a dictionary or a list.
        
        condition: A callable that takes an item (key-value pair for dictionaries, single item for lists)
            and returns a boolean. If True, the item is included in the result.

    Returns:
        A new collection of the same type as the input, containing only the items that meet the condition.

    Raises:
        TypeError: If the collection is neither a dictionary nor a list.

    """
    if isinstance(collection, Dict):
        return _filter_dict(collection, condition)
    elif isinstance(collection, List):
        return _filter_list(collection, condition)
    else:
        raise TypeError("The collection must be either a Dict or a List.")

# nested set, set value in nested dict or list
def nset(nested_structure: Union[List, Dict], indices: List[Union[int, str]], value: Any) -> None:
    """Sets a value in a nested list or dictionary structure.

    Navigates through the nested structure according to the specified indices and sets the
    value at the target location. The indices can be a mix of integers (for lists) and
    strings (for dictionaries).

    Args:
        nested_structure: The nested list or dictionary structure.
        
        indices: A list of indices to navigate through the structure.
        
        value: The value to set at the target location.

    Raises:
        ValueError: If the indices list is empty.
        
        TypeError: If the target container or the last index is of an incorrect type.
    """
    if not indices:
        raise ValueError("Indices list is empty, cannot determine target container")

    target_container = _get_target_container(nested_structure, indices[:-1])
    last_index = indices[-1]

    if isinstance(target_container, list):
        _ensure_list_index(target_container, last_index)
        target_container[last_index] = value
    elif isinstance(target_container, dict):
        target_container[last_index] = value
    else:
        raise TypeError("Cannot set value on non-list/dict element")

# nested get, get a value from a nested structure
def nget(nested_structure: Union[List, Dict], indices: List[Union[int, str]]) -> Any:
    """Retrieves a value from a nested list or dictionary structure.

    Navigates through the nested structure using the specified indices and retrieves the value
    at the target location. The indices can be integers for lists and strings for dictionaries.

    Args:
        nested_structure: The nested list or dictionary structure.
        
        indices: A list of indices to navigate through the structure.

    Returns:
        The value at the target location, or None if the target cannot be reached or does not exist.

    """
    try:
        target_container = _get_target_container(nested_structure, indices[:-1])
        last_index = indices[-1]

        if isinstance(target_container, list) and isinstance(last_index, int) and last_index < len(target_container):
            return target_container[last_index]
        elif isinstance(target_container, dict) and last_index in target_container:
            return target_container[last_index]
        else:
            return None  # Index out of bounds or not found
    except (IndexError, KeyError, TypeError):
        return None

def is_structure_homogeneous(
    structure: Any, 
    return_structure_type: bool = False
) -> Union[bool, Tuple[bool, Optional[type]]]:
    
    """
    Checks if a nested structure is homogeneous, meaning it doesn't contain a mix of lists and dictionaries.

    Args:
        structure: The nested structure to check.
        return_structure_type: Flag to indicate whether to return the type of homogeneous structure.

    Returns:
        If return_structure_type is False, returns a boolean indicating whether the structure is homogeneous.
        If return_structure_type is True, returns a tuple containing a boolean indicating whether the structure is homogeneous, and the type of the homogeneous structure if it is homogeneous (either list, dict, or None).
    """
    def _check_structure(substructure):
        structure_type = None
        if isinstance(substructure, list):
            structure_type = list
            for item in substructure:
                if not isinstance(item, structure_type) and isinstance(item, (list, dict)):
                    return False, None
                result, _ = _check_structure(item)
                if not result:
                    return False, None
        elif isinstance(substructure, dict):
            structure_type = dict
            for item in substructure.values():
                if not isinstance(item, structure_type) and isinstance(item, (list, dict)):
                    return False, None
                result, _ = _check_structure(item)
                if not result:
                    return False, None
        return True, structure_type

    is_homogeneous, structure_type = _check_structure(structure)
    if return_structure_type:
        return is_homogeneous, structure_type
    else:
        return is_homogeneous

# nested merge 
def nmerge(iterables: List[Union[Dict, List, Iterable]], 
            dict_update: bool = False, 
            dict_sequence: bool = False, 
            sequence_separator: str = '_', 
            sort_list: bool = False, 
            custom_sort: Callable[[Any], Any] = None) -> Union[Dict, List]:
    """Merges a list of dictionaries or sequences into a single dictionary or list.

    Args:
        iterables: A list of dictionaries or sequences to be merged.
        
        dict_update: If merging dictionaries, whether to overwrite values of the same key.
        
        dict_sequence: If merging dictionaries, whether to create unique keys for duplicate keys.
        
        sequence_separator: Separator for creating unique keys when dict_sequence is True.
        
        sort_list: If merging sequences, whether to sort the merged list.
        
        custom_sort: Custom sorting function for sorting the merged sequence.

    Returns:
        A merged dictionary or list based on the type of elements in iterables.

    Raises:
        TypeError: If the elements of iterables are not all of the same type.
    """
    if _is_homogeneous(iterables, Dict):
        return _merge_dicts(iterables, dict_update, dict_sequence, sequence_separator)
    elif _is_homogeneous(iterables, List) and not any(isinstance(it, (Dict, str)) for it in iterables):
        return _merge_sequences(iterables, sort_list, custom_sort)
    else:
        raise TypeError("All items in the input list must be of the same type, either Dict, List, or Iterable.")

# flatten dictionary
def flatten(obj: Any, parent_key: str = '', sep: str = '_', 
            max_depth: Union[int, None] = None, inplace: bool = False,
            dict_only: bool = False) -> Union[Dict, None]:
    if inplace:
        if not isinstance(obj, dict):
            raise ValueError("Object must be a dictionary when 'inplace' is True.")
        _dynamic_flatten_in_place(obj, parent_key, sep, max_depth, dict_only=dict_only)
    else:
        parent_key_tuple = tuple(parent_key.split(sep)) if parent_key else ()
        return dict(_dynamic_flatten_generator(obj, parent_key_tuple, sep, max_depth, dict_only=dict_only))

# unflatten dictionary
def unflatten(
    flat_dict: Dict[str, Any], sep: str = '_',
    custom_logic: Union[Callable[[str], Any], None] = None, 
    max_depth: Union[int, None] = None
) -> Union[Dict, List]:
    """
    Converts a flat dictionary with composite keys into a nested dictionary or list.

    Args:
        flat_dict (Dict[str, Any]): The flat dictionary to unflatten.
        
        sep (str, optional): Separator used in composite keys. Defaults to '_'.
        
        custom_logic (Union[Callable[[str], Any], None], optional): Custom function to process parts of the keys. Defaults to None.
        
        max_depth (Union[int, None], optional): Maximum depth for nesting. Defaults to None.
        
    Returns:
        Union[Dict, List]: The unflattened dictionary or list.
    """
    unflattened = {}
    for composite_key, value in flat_dict.items():
        parts = composite_key.split(sep)
        if custom_logic:
            parts = [custom_logic(part) for part in parts]
        else:
            parts = [int(part) if part.isdigit() else part for part in parts]

        if not unflattened and all(isinstance(part, int) for part in parts):
            unflattened = []

        ninsert(unflattened, parts, value, sep, max_depth)

    if isinstance(unflattened, dict) and all(isinstance(k, int) for k in unflattened.keys()):
        max_index = max(unflattened.keys(), default=-1)
        return [unflattened.get(i) for i in range(max_index + 1)]
    if not unflattened:
        return {}
    return unflattened


def ninsert(sub_obj: Union[Dict, List], parts: List[Union[str, int]], 
        value: Any, sep: str = '_', max_depth: Union[int, None] = None, current_depth: int = 0):
    """
    Recursively inserts a value into a nested structure (dictionary or list) based on 
    the specified path (parts).
    """
    parts_len = len(parts)
    parts_depth = 0
    for i, part in enumerate(parts[:-1]):
        if max_depth is not None and current_depth >= max_depth:
            break

        if isinstance(part, int):
            while len(sub_obj) <= part:
                sub_obj.append(None)
            if sub_obj[part] is None or not isinstance(sub_obj[part], (dict, list)):
                next_part = parts[i + 1]
                sub_obj[part] = [] if isinstance(next_part, int) else {}
            sub_obj = sub_obj[part]
        else:
            if part not in sub_obj:
                next_part = parts[i + 1]
                sub_obj[part] = [] if isinstance(next_part, int) else {}
            sub_obj = sub_obj[part]
        current_depth += 1
        parts_depth += 1

    if parts_depth < parts_len - 1:
        last_part = sep.join([str(part) for part in parts[parts_depth:]])
    else:
        last_part = parts[-1]
    if isinstance(last_part, int):
        _handle_list_insert(sub_obj, last_part, value)
    else:
        if isinstance(sub_obj, list):
            sub_obj.append({last_part: value})
        else:
            sub_obj[last_part] = value
        
def get_flattened_keys(obj: Any, sep: str = '_', max_depth: Union[int, None] = None, 
                    dict_only: bool = False, inplace: bool = False) -> List[str]:
    if inplace:
        obj_copy = deepcopy(obj)
        flatten(obj_copy, sep=sep, max_depth=max_depth, inplace=True, dict_only=dict_only)
        return list(obj_copy.keys())
    else:
        return list(flatten(obj, sep=sep, max_depth=max_depth, dict_only=dict_only).keys())

def _flatten_list(l: List, dropna: bool = True) -> List:
    """
    Flattens a nested list into a single-level list.

    Args:
        l (List): The nested list to flatten.
        dropna (bool, optional): If True, removes None values from the flattened list. Defaults to True.

    Returns:
        List: The flattened list, with or without None values based on the dropna parameter.
    """
    flattened_list = list(_flatten_list_generator(l, dropna))
    return _dropna(flattened_list) if dropna else flattened_list


def _dynamic_flatten_in_place(obj: Any, parent_key: str = '', sep: str = '_', 
                            max_depth: Union[int, None] = None, 
                            current_depth: int = 0, dict_only: bool = False) -> None:
    """
    Helper function to flatten the object in place.

    Args:
        obj (Any): The object to flatten.
        parent_key (str, optional): The base key for the flattened dictionary. Defaults to ''.
        sep (str, optional): Separator used in keys. Defaults to '_'.
        max_depth (Union[int, None], optional): Maximum depth to flatten. Defaults to None.
        current_depth (int, optional): Current depth in recursion. Defaults to 0.
        dict_only (bool, optional): If True, flattens only dictionaries. Defaults to False.

    Returns:
        None: This function modifies the input object in place and returns None.
    """
    if isinstance(obj, dict):
        keys_to_delete = []
        items = list(obj.items())  # Create a copy of the dictionary items

        for k, v in items:
            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            if isinstance(v, dict) and (max_depth is None or current_depth < max_depth):
                _dynamic_flatten_in_place(v, new_key, sep, max_depth, current_depth + 1, dict_only)
                keys_to_delete.append(k)
                obj.update(v)
            elif not dict_only and (isinstance(v, list) or not isinstance(v, (dict, list))):
                obj[new_key] = v
                if parent_key:
                    keys_to_delete.append(k)

        for k in keys_to_delete:
            del obj[k]
        
def _handle_list_insert(sub_obj: List, part: int, value: Any):
    """
    Inserts or replaces a value in a list at a specified index. If the index is 
    beyond the current size of the list, the list is extended with `None` values.

    Args:
        sub_obj (List): The list in which the value needs to be inserted.
        
        part (int): The index at which the value should be inserted.
        
        value (Any): The value to insert into the list.

    Returns:
        None: This function modifies the input list in place and returns None.
    """
    while len(sub_obj) <= part:
        sub_obj.append(None)
    sub_obj[part] = value
        
def _convert_to_int_if_possible(s: str) -> Union[int, str]:
    """
    Converts a string to an integer if possible; otherwise, returns the string.

    Args:
        s (str): The string to convert.

    Returns:
        Union[int, str]: The converted integer or the original string.
    """
    return int(s) if s.lstrip('-').isdigit() else s

def _is_iterable(obj) -> bool:
    return isinstance(obj, Iterable) and not isinstance(obj, str)

def _ensure_list_index(lst: List, index: int, default=None) -> None:
    """Ensures that a list is at least as long as a specified index.

    This method appends the default value to the list until its length is at least
    equal to the specified index + 1. This ensures that accessing the list at the
    specified index will not result in an IndexError.

    Args:
        lst: The list to be modified.
        
        index: The index the list should extend to.
        
        default: The default value to append to the list. Defaults to None.

    """
    while len(lst) <= index:
        lst.append(default)
        
def _deep_update(original: Dict, update: Dict) -> Dict:
    """Recursively updates a dictionary with another dictionary.

    For each key-value pair in the update dictionary, this method updates the original dictionary.
    If the value corresponding to a key is itself a dictionary, the update is applied recursively.

    Args:
        original: The original dictionary to be updated.
        
        update: The dictionary with updates to be applied.

    Returns:
        The updated dictionary with the values from the update dictionary applied.
        
    """
    for key, value in update.items():
        if isinstance(value, dict) and key in original:
            original[key] = _deep_update(original.get(key, {}), value)
        else:
            original[key] = value
    return original

def _dynamic_flatten_generator(obj: Any, parent_key: Tuple[str, ...], sep: str = '_', 
                                max_depth: Union[int, None] = None, current_depth: int = 0, 
                                dict_only: bool = False
                            ) -> Generator[Tuple[str, Any], None, None]:
    """A generator to flatten a nested dictionary or list into key-value pairs.

    This method recursively traverses the nested dictionary or list and yields flattened key-value pairs.

    Args:
        obj: The nested object (dictionary or list) to flatten.
        parent_key: Tuple of parent keys leading to the current object.
        sep: Separator used between keys in the flattened output.
        max_depth: Maximum depth to flatten. None indicates no depth limit.
        current_depth: The current depth level in the nested object.
        dict_only: If True, only processes nested dictionaries, skipping other types in lists.

    Yields:
        Tuple[str, Any]: Flattened key-value pair as a tuple.
    """
    if max_depth is not None and current_depth > max_depth:
        yield sep.join(parent_key), obj
        return

    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = parent_key + (k,)
            yield from _dynamic_flatten_generator(v, new_key, sep, max_depth, current_depth + 1, dict_only)
    elif isinstance(obj, list) and not dict_only:
        for i, item in enumerate(obj):
            new_key = parent_key + (str(i),)
            yield from _dynamic_flatten_generator(item, new_key, sep, max_depth, current_depth + 1, dict_only)
    else:
        yield sep.join(parent_key), obj

def _deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Merges two dictionaries deeply.

    For each key in `dict2`, updates or adds the key-value pair to `dict1`. If values 
    for the same key are dictionaries, merge them recursively.

    Args:
        dict1: The dictionary to be updated.
        dict2: The dictionary with values to update `dict1`.

    Returns:
        The updated dictionary `dict1`.
    """
    for key in dict2:
        if key in dict1:
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                _deep_merge_dicts(dict1[key], dict2[key])
            else:
                dict1[key] = dict2[key]
        else:
            dict1[key] = dict2[key]
    return dict1

def _extend_list_to_index(lst: List[Any], index: int, fill_value: Any = None) -> None:
    """
    Extends a list to a specified index with a fill value.

    Args:
        lst (List[Any]): The list to extend.
        index (int): The index to extend the list to.
        fill_value (Any, optional): The value to fill the extended part of the list with. Defaults to None.

    Returns:
        None: This function modifies the input list in place and returns None.
    """
    while len(lst) <= index:
        lst.append(fill_value)
            
def _dropna(l: List) -> List:
    """
    Removes None values from a list.

    Args:
        l (List): The list to remove None values from.

    Returns:
        List: A new list with None values removed.
    """
    return [item for item in l if item is not None]

def _flatten_list_generator(l: List, dropna: bool = True) -> Generator[Any, None, None]:
    """
    Generator to flatten a nested list.

    Args:
        l (List): The nested list to flatten.
        dropna (bool, optional): If True, removes None values during the flattening process. Defaults to True.

    Yields:
        Generator[Any, None, None]: Yields elements of the flattened list.
    """
    for i in l:
        if isinstance(i, list):
            yield from _flatten_list_generator(i, dropna)
        else:
            yield i
            
def _is_homogeneous(iterables: List[Union[Dict, List, Iterable]], type_check: type) -> bool:
    """Checks if all elements in a list are of the same specified type.

    Args:
        iterables: A list of elements to check.
        type_check: The type to check against.

    Returns:
        True if all elements in the list are of the specified type; otherwise False.
    """
    return all(isinstance(it, type_check) for it in iterables)

def _merge_dicts(iterables: List[Dict[Any, Any]], dict_update: bool, dict_sequence: bool, sequence_separator: str) -> Dict[Any, Any]:
    """Merges a list of dictionaries into a single dictionary.

    Args:
        iterables: A list of dictionaries to be merged.
        dict_update: If True, the value of a key in a later dictionary overwrites the previous one.
        dict_sequence: If True, instead of overwriting, keys are made unique by appending a sequence number.
        sequence_separator: The separator to use when creating unique keys in case of dict_sequence.

    Returns:
        A merged dictionary containing the combined key-value pairs from all dictionaries in the list.
    """
    merged_dict = {}
    sequence_counters = defaultdict(int)
    
    for d in iterables:
        for key, value in d.items():
            if key not in merged_dict or dict_update:
                merged_dict[key] = value
            elif dict_sequence:
                sequence_counters[key] += 1
                new_key = f"{key}{sequence_separator}{sequence_counters[key]}"
                merged_dict[new_key] = value
                
    return merged_dict

def _merge_sequences(iterables: List[Iterable], sort_list: bool, custom_sort: Callable[[Any], Any] = None) -> List:
    """Merges a list of sequences (like lists) into a single list.

    Args:
        iterables: A list of iterables to be merged.
        sort_list: If True, the merged list will be sorted.
        custom_sort: A custom sorting function; used only if sort_list is True.

    Returns:
        A merged list containing elements from all iterables in the list.
    """
    merged_list = list(chain(*iterables))
    if sort_list:
        if custom_sort:
            return sorted(merged_list, key=custom_sort)
        
        else:
            return sorted(merged_list, key=lambda x: (isinstance(x, str), x))
    return merged_list

def _filter_dict(dictionary: Dict[Any, Any], condition: Callable[[Any], bool]) -> Dict[Any, Any]:
    """Filters a dictionary based on a given condition.

    This static method iterates over each key-value pair in the dictionary and retains
    those pairs where the condition function returns True.

    Args:
        dictionary: A dictionary to filter.
        
        condition: A callable that takes a key-value pair tuple and returns a boolean.
            If True, the pair is included in the result.

    Returns:
        A new dictionary containing only the key-value pairs that meet the condition.

    """
    return {k: v for k, v in dictionary.items() if condition((k, v))}

def _filter_list(lst: List[Any], condition: Callable[[Any], bool]) -> List[Any]:
    """Filters a list based on a given condition.

    Iterates over each item in the list and includes it in the result if the condition function
    returns True for that item.

    Args:
        lst: A list to filter.
        
        condition: A callable that takes an item from the list and returns a boolean.
            If True, the item is included in the result.

    Returns:
        A new list containing only the items that meet the condition.

    """
    return [item for item in lst if condition(item)]

def _get_target_container(nested_list: Union[List, Dict], indices: List[Union[int, str]]) -> Union[List, Dict]:
    current_element = nested_list
    for index in indices:
        if isinstance(current_element, list):
            if isinstance(index, int) and 0 <= index < len(current_element):
                current_element = current_element[index]
            else:
                raise IndexError("List index out of range")
        elif isinstance(current_element, dict):
            if index in current_element:
                current_element = current_element[index]
            else:
                raise KeyError("Key not found in dictionary")
        else:
            raise TypeError("Current element is neither a list nor a dictionary")
    return current_element


# def nprint(nested_structure: Union[Dict, Iterable], indent: int = 0) -> None:
#     if isinstance(nested_structure, dict):
#         nprint(_print_dict(nested_structure, indent))
#     elif _is_iterable(nested_structure):
#         nprint(" " * indent + "[")
#         nprint(_print_iterable(nested_structure, indent + 2))
#         nprint(" " * indent + "]")
#     else:
#         nprint(f"{' ' * indent}{repr(nested_structure)}")

# def _print_dict(nested_dict: Dict, indent: int) -> str:
#     lines = [" " * indent + "{"]
#     items = list(nested_dict.items())
#     for index, (key, value) in enumerate(items):
#         line_end = "," if index < len(items) - 1 else ""
#         if isinstance(value, dict):
#             lines.append(f"{' ' * (indent + 2)}{repr(key)}: {{")
#             lines.append(_print_dict(value, indent + 4))
#             lines.append(f"{' ' * (indent + 2)}}}{line_end}")
#         elif _is_iterable(value):
#             lines.append(f"{' ' * (indent + 2)}{repr(key)}: [")
#             lines.append(_print_iterable(value, indent + 4))
#             lines.append(f"{' ' * (indent + 2)}]{line_end}")
#         else:
#             lines.append(f"{' ' * (indent + 2)}{repr(key)}: {repr(value)}{line_end}")
#     lines.append(" " * indent + "}")
#     return "\n".join(lines)

# @staticmethod
# def _print_iterable(iterable: Iterable, indent: int) -> str:
#     lines = []
#     iterable_list = list(iterable)
#     for index, item in enumerate(iterable_list):
#         line_end = "," if index < len(iterable_list) - 1 else ""
#         if isinstance(item, dict):
#             lines.append(_print_dict(item, indent + 2) + line_end)
#         elif _is_iterable(item):
#             lines.append(" " * indent + "[")
#             lines.append(_print_iterable(item, indent + 2))
#             lines.append(f"{' ' * indent}]{line_end}")
#         else:
#             lines.append(f"{' ' * indent}{repr(item)}{line_end}")
#     return "\n".join(lines)

# def _tuples_to_dict(tuples_list: List[Tuple[str, Any]]) -> Dict:
#     """Converts a list of tuples into a dictionary.

#     Each tuple in the list should be a key-value pair, where the key is a string
#     that represents the nested keys separated by underscores.

#     Args:
#         tuples_list: A list of tuples where each tuple is a (key, value) pair.

#     Returns:
#         A dictionary created from the tuples.
#     """
#     result_dict = {}
#     for key, value in tuples_list:
#         ninsert(result_dict, key.split('_'), value)
#     return result_dict


# @staticmethod
# def _insert_with_dict_handling(result_list: Union[Dict, List], 
#                             indices: List[Union[int, str]], 
#                             value: Any, 
#                             current_depth: int = 0):
#     """
#     Helper function to insert a value into a list or dictionary at a nested location 
#     defined by indices.

#     Args:
#         result_list (Union[Dict, List]): The list or dictionary to insert into.
#         indices (List[Union[int, str]]): The indices defining where to insert the value.
#         value (Any): The value to insert.
#         current_depth (int, optional): The current depth in the nested structure. Defaults to 0.

#     Returns:
#         None: This function modifies the input list or dictionary in place and returns None.
#     """
#     for index in indices[:-1]:
#         if isinstance(result_list, list):
#             _extend_list_to_index(result_list, index, [])
#             result_list = result_list[index]
#         elif isinstance(result_list, dict):
#             result_list = result_list.setdefault(index, {})
#         current_depth += 1
#     last_index = indices[-1]
#     if isinstance(result_list, list):
#         _extend_list_to_index(result_list, last_index)
#         result_list[last_index] = value
#     else:
#         result_list[last_index] = value