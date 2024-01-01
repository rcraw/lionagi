import json
from typing import Union, Callable, List, Dict, Any
from lionagi.schema.base_schema import T, DataNode


def from_langchain(lc_doc: Any) -> T:
    """
    Converts a langchain document into a DataNode object.

    Parameters:
        lc_doc (Any): The langchain document to be converted.

    Returns:
        DataNode: A DataNode object created from the langchain document.
    """
    info_json = lc_doc.to_json()
    info_node = {'lc_id': info_json['id']}
    info_node = {**info_node, **info_json['kwargs']}
    return DataNode(**info_node)

def to_langchain_document(datanode: T, **kwargs: Any) -> Any:
    """
    Converts a DataNode into a langchain Document.

    Parameters:
        datanode (DataNode): The DataNode to be converted.
        **kwargs: Additional keyword arguments to be included in the Document.

    Returns:
        Any: A langchain Document created from the DataNode.
    """
    from langchain.schema import Document

    dnode = json.loads(datanode.to_json())
    dnode['page_content'] = dnode.pop('content')
    dnode = {**dnode, **kwargs}
    return Document(**dnode)

def langchain_loader(loader: Union[str, Callable], 
                     loader_args: List[Any] = [], 
                     loader_kwargs: Dict[str, Any] = {}) -> Any:
    """
    Loads data using a specified langchain loader.

    Parameters:
        loader (Union[str, Callable]): The name of the loader function or the loader function itself.
        loader_args (List[Any]): Positional arguments to pass to the loader function.
        loader_kwargs (Dict[str, Any]): Keyword arguments to pass to the loader function.

    Returns:
        Any: The data loaded by the loader function.

    Raises:
        ValueError: If the specified loader is invalid or if the loader fails to load data.
    """
    import langchain.document_loaders as document_loaders

    try:
        if isinstance(loader, str):
            loader = getattr(document_loaders, loader)
        else:
            loader = loader
    except Exception as e:
        raise ValueError(f'Invalid loader: {loader}. Error: {e}')

    try:
        loader_obj = loader(*loader_args, **loader_kwargs)
        data = loader_obj.load()
        return data
    except Exception as e:
        raise ValueError(f'Failed to load. Error: {e}')

def langchain_text_splitter(data: str, 
                            splitter: Union[str, Callable], 
                            splitter_args: List[Any] = [], 
                            splitter_kwargs: Dict[str, Any] = {}) -> List[str]:
    """
    Splits text using a specified langchain text splitter.

    Parameters:
        data (str): The text data to split.
        splitter (Union[str, Callable]): The name of the splitter function or the splitter function itself.
        splitter_args (List[Any]): Positional arguments to pass to the splitter function.
        splitter_kwargs (Dict[str, Any]): Keyword arguments to pass to the splitter function.

    Returns:
        List[str]: The list of text chunks after splitting.

    Raises:
        ValueError: If the specified splitter is invalid or if the splitter fails to split the text.
    """
    import langchain.text_splitter as text_splitter

    try:
        if isinstance(splitter, str):
            splitter = getattr(text_splitter, splitter)
        else:
            splitter = splitter
    except Exception as e:
        raise ValueError(f'Invalid text splitter: {text_splitter}. Error: {e}')

    try:
        splitter_obj = splitter(*splitter_args, **splitter_kwargs)
        chunk = splitter_obj.split_text(data)
        return chunk
    except Exception as e:
        raise ValueError(f'Failed to split. Error: {e}')

def langchain_code_splitter(doc: str, 
                            language: str, 
                            splitter_args: List[Any] = [], 
                            splitter_kwargs: Dict[str, Any] = {}) -> List[Any]:
    """
    Splits code into smaller chunks using a RecursiveCharacterTextSplitter specific to a language.

    Parameters:
        doc (str): The code document to be split.
        language (str): The programming language of the code.
        splitter_args (List[Any]): Positional arguments to pass to the splitter.
        splitter_kwargs (Dict[str, Any]): Keyword arguments to pass to the splitter.

    Returns:
        List[Any]: A list of Documents, each representing a chunk of the original code.

    Raises:
        ValueError: If the splitter fails to split the code document.
    """
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    try:
        splitter = RecursiveCharacterTextSplitter.from_language(
            language=language, *splitter_args, **splitter_kwargs
            )
        docs = splitter.create_documents([doc])
        return docs
    except Exception as e:
        raise ValueError(f'Failed to split. Error: {e}')
    