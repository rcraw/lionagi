from __future__ import annotations

from pathlib import Path
from typing import Any, ClassVar, Literal

import pandas as pd
from lion_core.generic.component import Component as CoreComponent
from lionfuncs import LN_UNDEFINED, to_dict
from pydantic import Field
from typing_extensions import Annotated, deprecated

from ._adapter_registry.component.adapter_registry import ComponentAdapterRegistry

NAMED_FIELD = Annotated[str, Field(..., alias="field")]


class Component(CoreComponent):

    _adapter_registry: ClassVar = ComponentAdapterRegistry

    @classmethod
    def from_obj(
        cls,
        obj: Any,
        /,
        handle_how: Literal["suppress", "raise", "coerce", "coerce_key"] = "raise",
        **kwargs: Any,
    ) -> Component | list[Component]:
        if isinstance(obj, pd.DataFrame):
            obj = [i for _, i in obj.iterrows()]
        if isinstance(obj, (list, tuple)) and len(obj) > 1:
            return [
                cls._dispatch_from_obj(i, handle_how=handle_how, **kwargs) for i in obj
            ]

        return cls._dispatch_from_obj(obj, handle_how=handle_how, **kwargs)

    @classmethod
    def _dispatch_from_obj(
        cls,
        obj: Any,
        /,
        handle_how: Literal["suppress", "raise", "coerce", "coerce_key"] = "raise",
        **kwargs: Any,
    ) -> Component:
        try:
            type_ = str(type(obj))

            if "langchain" in type_:
                return cls.adapt_from(obj, "langchain", **kwargs)

            if "llamaindex" in type_:
                return cls.adapt_from(obj, "llamaindex", **kwargs)

            obj = cls._obj_to_dict(obj, **kwargs)
            return cls.from_dict(obj)

        except Exception as e:
            if handle_how == "raise":
                raise e
            if handle_how == "coerce":
                return cls.from_dict({"content": obj})
            if handle_how == "suppress":
                return None
            if handle_how == "coerce_key":
                return cls.from_dict({str(k): v for k, v in obj.items()})

    def _obj_to_dict(cls, obj: Any, /, **kwargs) -> dict:
        dict_ = None

        if isinstance(obj, pd.Series):
            return cls._get_adapter_registry().adapt_from(
                cls, obj, "pd_series", **kwargs
            )

        if isinstance(obj, Path):
            suffix = Path(obj).suffix.lower().strip(".").strip() + "_file"
            if suffix in cls._get_adapter_registry().list_adapters():
                return cls._get_adapter_registry().adapt_from(
                    cls, obj, suffix, **kwargs
                )
            raise ValueError(f"Unsupported file type: {obj.suffix}")

        if isinstance(obj, str) and "." in obj:
            suffix = obj.split(".")[-1].lower().strip() + "_file"
            if suffix in cls._get_adapter_registry().list_adapters():
                return cls._get_adapter_registry().adapt_from(
                    cls, obj, suffix, **kwargs
                )

        if isinstance(obj, str):
            kwargs["suppress"] = True
            if "{" in obj and "}" in obj:
                dict_ = cls._get_adapter_registry().adapt_from(
                    cls, obj, "json", **kwargs
                )
            if not dict_ and "<" in obj and ">" in obj:
                dict_ = cls._get_adapter_registry().adapt_from(
                    cls, obj, "xml", **kwargs
                )
            if isinstance(dict_, dict):
                return dict_
            else:
                msg = obj[:100] + "..." if len(obj) > 100 else obj
                raise ValueError(
                    f"The value input cannot be converted to a valid dict: {msg}"
                )

        kwargs["suppress"] = True
        dict_ = to_dict(obj, **kwargs)
        if not dict_:
            raise ValueError(f"Unsupported object type: {type(obj)}")
        return dict_

    # legacy methods (for backward compatibility )

    @property
    @deprecated(
        "Use Component.all_fields instead", category=DeprecationWarning, stacklevel=2
    )
    def _all_fields(self):
        return self.all_fields

    @property
    @deprecated(
        "Use Component.field_annotation instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def _field_annotations(self) -> dict[str, Any]:
        return self.field_annotation(list(self.all_fields.keys()))

    @deprecated(
        "Use Component.convert_to('json') instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def to_json_str(self, **kwargs: Any) -> str:
        return self.convert_to("json", **kwargs)

    @deprecated(
        "Use Component.convert_to('json_file') instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def to_json_file(self, **kwargs: Any) -> str:
        return self.convert_to("json_file", **kwargs)

    @deprecated(
        "Use Component.convert_to('xml') instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def to_xml(self, **kwargs: Any) -> str:
        return self.convert_to("xml", **kwargs)

    @deprecated(
        "Use Component.convert_to('xml_file') instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def to_xml_file(self, **kwargs: Any) -> str:
        return self.convert_to("xml_file", **kwargs)

    @deprecated(
        "Use Component.convert_to('pd_series') instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def to_pd_series(self, **kwargs: Any) -> str:
        return self.convert_to("pd_series", **kwargs)

    @deprecated(
        "Use Component.convert_to('llamaindex') instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def to_llama_index_node(self, **kwargs: Any) -> str:
        return self.convert_to("llamaindex", **kwargs)

    @deprecated(
        "Use Component.convert_to('langchain') instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def to_langchain_doc(self, **kwargs: Any) -> str:
        return self.convert_to("langchain", **kwargs)

    @deprecated(
        "Use Component.metadata.pop() instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def _meta_pop(self, indices, default=LN_UNDEFINED):
        return self.metadata.pop(indices, default)

    @deprecated(
        "Use Component.metadata.insert() instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def _meta_insert(self, indices, value):
        self.metadata.insert(indices, value)

    @deprecated(
        "Use Component.metadata.set() instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def _meta_set(self, indices, value):
        self.metadata.set(indices, value)

    @deprecated(
        "Use Component.metadata.get() instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def _meta_get(self, indices, default=LN_UNDEFINED):
        return self.metadata.get(indices, default)

    @deprecated(
        "Use Component.field_hasattr() instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def _field_has_attr(self, k, attr) -> bool:
        return self.field_hasattr(k, attr)

    @deprecated(
        "Use Component.field_getattr() instead",
        category=DeprecationWarning,
        stacklevel=2,
    )
    def _get_field_attr(self, k, attr, default=LN_UNDEFINED):
        return self.field_getattr(k, attr, default)

    @deprecated(
        "Use Component.add_field() instead", category=DeprecationWarning, stacklevel=2
    )
    def _add_field(
        self,
        field: str,
        annotation: Any = LN_UNDEFINED,
        default: Any = LN_UNDEFINED,
        value: Any = LN_UNDEFINED,
        field_obj: Any = LN_UNDEFINED,
        **kwargs,
    ) -> None:
        kwargs["default"] = default
        self.add_field(
            field,
            value=value,
            annotation=annotation,
            field_obj=field_obj,
            **kwargs,
        )


__all__ = ["Component"]
