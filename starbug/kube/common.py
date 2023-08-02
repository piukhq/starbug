from pydantic import BaseModel, ConfigDict


def to_camel(string: str) -> str:
    """Convert Python style veriables to camelCase."""
    upper = "".join(word.capitalize() for word in string.split("_"))
    return upper[:1].lower() + upper[1:]


Labels = dict[str, str]


class KubernetesModel(BaseModel):
    """Shared Model for all Kuberentes BaseModels."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
