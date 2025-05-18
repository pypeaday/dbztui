#!/usr/bin/env -S uv run --quiet --script
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "ninesui @ git+https://github.com/waylonwalker/ninesui.git",
#     "httpx",
#     "deep-translator",
# ]
# ///
from typing import Optional, List, TypeVar, ClassVar, Any, Dict
from pydantic import BaseModel, Field, HttpUrl
import httpx
from textual import log
from ninesui import CommandSet, Command, NinesUI
from functools import lru_cache
from deep_translator import GoogleTranslator
import json
import os

BASE_URL = "https://dragonball-api.com/api/"
LANGUAGE = "en"

# Translation cache file
CACHE_DIR = os.path.expanduser("~/.cache/dbztui")
CACHE_FILE = os.path.join(CACHE_DIR, "translation_cache.json")

# Create cache directory if it doesn't exist
os.makedirs(CACHE_DIR, exist_ok=True)

# Load translation cache from file
translation_cache: Dict[str, str] = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            translation_cache = json.load(f)
    except Exception as e:
        log(f"Error loading translation cache: {e}")

# Initialize translator
translator = GoogleTranslator(source='es', target='en')

T = TypeVar("T", bound="DBZResource")

@lru_cache(maxsize=1000)
def translate_text(text: str) -> str:
    """Translate text from Spanish to English with caching"""
    if not text or len(text) < 5:  # Don't translate very short texts
        return text
        
    # Check if translation is in cache
    if text in translation_cache:
        return translation_cache[text]
    
    try:
        # Translate text
        translated = translator.translate(text)
        
        # Save to cache
        translation_cache[text] = translated
        
        # Periodically save cache to file
        if len(translation_cache) % 10 == 0:  # Save every 10 new translations
            try:
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(translation_cache, f, ensure_ascii=False, indent=2)
            except Exception as e:
                log(f"Error saving translation cache: {e}")
                
        return translated
    except Exception as e:
        log(f"Translation error: {e}")
        return text  # Return original text if translation fails


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
        
        # Translate description if present
        if "description" in data and data["description"]:
            data["description"] = translate_text(data["description"])
            
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
    
    def __init__(self, **data):
        # Translate description before initializing
        if "description" in data and data["description"]:
            data["description"] = translate_text(data["description"])
        super().__init__(**data)
    
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
    
    def __init__(self, **data):
        # Translate description before initializing
        if "description" in data and data["description"]:
            data["description"] = translate_text(data["description"])
        super().__init__(**data)


class Saga(DBZResource):
    name: str
    description: str
    image: Optional[HttpUrl] = None
    chapters: Optional[List[int]] = None
    deletedAt: Optional[str] = None
    
    def __init__(self, **data):
        # Translate description before initializing
        if "description" in data and data["description"]:
            data["description"] = translate_text(data["description"])
        super().__init__(**data)


class Episode(DBZResource):
    name: str
    description: str
    chapter: int
    saga: str
    deletedAt: Optional[str] = None
    
    def __init__(self, **data):
        # Translate description before initializing
        if "description" in data and data["description"]:
            data["description"] = translate_text(data["description"])
        super().__init__(**data)


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
    try:
        ui.run()
    finally:
        # Save translation cache when exiting
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(translation_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log(f"Error saving translation cache on exit: {e}")
