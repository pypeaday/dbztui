#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "ninesui @ git+https://github.com/waylonwalker/ninesui.git",
#     "httpx",
# ]
# ///
from typing import Optional, List, TypeVar, ClassVar, Any
from pydantic import BaseModel, Field, HttpUrl
import httpx
from textual import log
from ninesui import CommandSet, Command, NinesUI

BASE_URL = "https://dragonball-api.com/api/"
LANGUAGE = "en"

T = TypeVar("T", bound="DBZResource")


class DBZResource(BaseModel):
    id: int

    nines_config: ClassVar[dict] = {"bindings": {}}

    @classmethod
    def fetch(cls, ctx=None):
        endpoint = cls.__name__.lower() + "s"
        
        client = httpx.Client()
        log(f"Fetching {endpoint}")

        if ctx:
            if hasattr(ctx, endpoint):
                result = []
                for url in getattr(ctx, endpoint):
                    res = client.get(str(url), params={"language": LANGUAGE}).json()
                    result.append(cls(**res))
                return result

        url = f"{BASE_URL}{endpoint}"
        params = {"language": LANGUAGE}

        results: List[T] = []
        response = client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Handle pagination structure from Dragon Ball API
        if "items" in data:
            results.extend(cls(**item) for item in data.get("items", []))
            
            # Fetch all pages if needed
            while data.get("links", {}).get("next"):
                next_url = data["links"]["next"]
                # The next URL might already include language param, but we'll ensure it's there
                if "language=" not in next_url:
                    separator = "&" if "?" in next_url else "?"
                    next_url = f"{next_url}{separator}language={LANGUAGE}"
                response = client.get(next_url)
                response.raise_for_status()
                data = response.json()
                results.extend(cls(**item) for item in data.get("items", []))
        else:
            # Direct list of items
            results.extend(cls(**item) for item in data)

        return results

    def hover(self):
        return self
    
    def get_details(self):
        """Get detailed information about this resource"""
        client = httpx.Client()
        endpoint = self.__class__.__name__.lower() + "s"
        url = f"{BASE_URL}{endpoint}/{self.id}"
        response = client.get(url, params={"language": LANGUAGE})
        response.raise_for_status()
        data = response.json()
        return self.__class__(**data)


class Character(DBZResource):
    name: str
    ki: str
    maxKi: str
    race: str
    gender: str
    description: str
    image: Optional[HttpUrl] = None
    affiliation: str
    deletedAt: Optional[str] = None
    
    nines_config: ClassVar[dict] = {"bindings": {"t": "get_transformations"}}
    
    def get_transformations(self):
        """Get all transformations for this character"""
        client = httpx.Client()
        url = f"{BASE_URL}characters/{self.id}/transformations"
        try:
            response = client.get(url, params={"language": LANGUAGE})
            response.raise_for_status()
            data = response.json()
            if "items" in data:
                return [Transformation(**item) for item in data.get("items", [])]
            return [Transformation(**item) for item in data]
        except Exception as e:
            log(f"Error fetching transformations: {e}")
            return []


class Transformation(DBZResource):
    name: str
    image: Optional[HttpUrl] = None
    ki: str
    characterId: int
    deletedAt: Optional[str] = None


class Planet(DBZResource):
    name: str
    description: str
    image: Optional[HttpUrl] = None
    deletedAt: Optional[str] = None


class Saga(DBZResource):
    name: str
    description: str
    image: Optional[HttpUrl] = None
    chapters: Optional[List[int]] = None
    deletedAt: Optional[str] = None


class Episode(DBZResource):
    name: str
    description: str
    chapter: int
    saga: str
    deletedAt: Optional[str] = None


commands = CommandSet(
    [
        Command(
            name="character",
            aliases=["c"],
            model=Character,
            is_default=True,
        ),
        Command(
            name="transformation",
            aliases=["t"],
            model=Transformation,
        ),
        Command(
            name="planet",
            aliases=["p"],
            model=Planet,
        ),
        Command(
            name="saga",
            aliases=["s"],
            model=Saga,
        ),
        Command(
            name="episode",
            aliases=["e"],
            model=Episode,
        ),
    ]
)

metadata = {
    "title": "Dragon Ball Z Explorer",
    "subtitle": "Use :character to list characters. Enter to drill in. Escape to go back/quit.",
}


if __name__ == "__main__":
    ui = NinesUI(metadata=metadata, commands=commands)
    ui.run()
