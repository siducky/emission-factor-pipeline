

# Python Development Patterns

Idiomatic Python patterns, PEP 8 standards, type hints, and best practices for building robust, efficient, and maintainable Python applications.

## When to use

- When writing new Python code.
- When reviewing Python code.
- When refactoring existing Python code.
- When designing Python packages/modules.

## Core Principles

### 1. Readability is Key

Python prioritizes readability. Code should be obvious and easy to understand.

```python
# Good: Clear and readable
def get_active_users(users: list[User]) -> list[User]:
    """Return only active users from the provided list."""
    return [user for user in users if user.is_active]


# Bad: Clever but confusing
def get_active_users(u):
    return [x for x in u if x.a]
```

### 2. Explicit is better than Implicit

Avoid magic; make it clear what the code is doing.

```python
# Good: Explicit configuration
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Bad: Hidden side effects
import some_module

some_module.setup()  # What does this do?
```

### 3. EAFP - Easier to Ask for Forgiveness than Permission

Python prefers exception handling over condition checks.

```python
# Good: EAFP style
def get_value(dictionary: dict, key: str) -> Any:
    try:
        return dictionary[key]
    except KeyError:
        return default_value


# Bad: LBYL (Look Before You Leap) style
def get_value(dictionary: dict, key: str) -> Any:
    if key in dictionary:
        return dictionary[key]
    else:
        return default_value
```

## Type Hints

### Basic Type Annotations

```python
from typing import Optional, List, Dict, Any


def process_user(
    user_id: str, data: Dict[str, Any], active: bool = True
) -> Optional[User]:
    """Process a user and return the updated User or None."""
    if not active:
        return None
    return User(user_id, data)
```

### Modern Type Hints (Python 3.9+)

```python
# Python 3.9+ - Use built-in types
def process_items(items: list[str]) -> dict[str, int]:
    return {item: len(item) for item in items}


# Python 3.8 and earlier - Use typing module
from typing import List, Dict


def process_items(items: List[str]) -> Dict[str, int]:
    return {item: len(item) for item in items}
```

### Type Aliases and TypeVar

```python
from typing import TypeVar, Union

# Type alias for complex types
JSON = Union[dict[str, Any], list[Any], str, int, float, bool, None]


def parse_json(data: str) -> JSON:
    return json.loads(data)


# Generic types
T = TypeVar("T")


def first(items: list[T]) -> T | None:
    """Return the first item or None if list is empty."""
    return items[0] if items else None
```

### Protocol-based Duck Typing

```python
from typing import Protocol


class Renderable(Protocol):
    def render(self) -> str:
        """Render the object to a string."""


def render_all(items: list[Renderable]) -> str:
    """Render all items that implement the Renderable protocol."""
    return "\n".join(item.render() for item in items)
```

## Error Handling Patterns

### Catching Specific Exceptions

```python
# Good: Catch specific exceptions
def load_config(path: str) -> Config:
    try:
        with open(path) as f:
            return Config.from_json(f.read())
    except FileNotFoundError as e:
        raise ConfigError(f"Config file not found: {path}") from e
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in config: {path}") from e


# Bad: Bare except
def load_config(path: str) -> Config:
    try:
        with open(path) as f:
            return Config.from_json(f.read())
    except:
        return None  # Silent failure!
```

### Exception Chaining

```python
def process_data(data: str) -> Result:
    try:
        parsed = json.loads(data)
    except json.JSONDecodeError as e:
        # Chain exceptions to preserve the traceback
        raise ValueError(f"Failed to parse data: {data}") from e
```

### Custom Exception Hierarchy

```python
class AppError(Exception):
    """Base exception for all application errors."""

    pass


class ValidationError(AppError):
    """Raised when input validation fails."""

    pass


class NotFoundError(AppError):
    """Raised when a requested resource is not found."""

    pass


# Usage
def get_user(user_id: str) -> User:
    user = db.find_user(user_id)
    if not user:
        raise NotFoundError(f"User not found: {user_id}")
    return user
```

## Context Managers

### Resource Management

```python
# Good: Using context managers
def process_file(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


# Bad: Manual resource management
def process_file(path: str) -> str:
    f = open(path, "r")
    try:
        return f.read()
    finally:
        f.close()
```

### Custom Context Managers

```python
from contextlib import contextmanager


@contextmanager
def timer(name: str):
    """Context manager to time a block of code."""
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    print(f"{name} took {elapsed:.4f} seconds")


# Usage
with timer("data processing"):
    process_large_dataset()
```

### Context Manager Classes

```python
class DatabaseTransaction:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        self.connection.begin_transaction()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.connection.commit()
        else:
            self.connection.rollback()
        return False  # Don't suppress exceptions


# Usage
with DatabaseTransaction(conn):
    user = conn.create_user(user_data)
    conn.create_profile(user.id, profile_data)
```

## Comprehensions and Generators

### List Comprehensions

```python
# Good: List comprehension for simple transformations
names = [user.name for user in users if user.is_active]

# Bad: Manual loop
names = []
for user in users:
    if user.is_active:
        names.append(user.name)

# Complex comprehensions should be expanded
# Bad: Too complex
result = [x * 2 for x in items if x > 0 if x % 2 == 0]


# Good: Use a generator function
def filter_and_transform(items: Iterable[int]) -> list[int]:
    result = []
    for x in items:
        if x > 0 and x % 2 == 0:
            result.append(x * 2)
    return result
```

### Generator Expressions

```python
# Good: Generator for lazy evaluation
total = sum(x * x for x in range(1_000_000))

# Bad: Creates large intermediate list
total = sum([x * x for x in range(1_000_000)])
```

### Generator Functions

```python
def read_large_file(path: str) -> Iterator[str]:
    """Read a large file line by line."""
    with open(path) as f:
        for line in f:
            yield line.strip()


# Usage
for line in read_large_file("huge.txt"):
    process(line)
```

## Data Classes and Named Tuples

### Data Classes

```python
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class User:
    """User entity with automatic __init__, __repr__, and __eq__."""

    id: str
    name: str
    email: str
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
```

### Data Classes with Validation

```python
@dataclass
class User:
    email: str
    age: int

    def __post_init__(self):
        if "@" not in self.email:
            raise ValueError(f"Invalid email: {self.email}")
        if self.age < 0 or self.age > 150:
            raise ValueError(f"Invalid age: {self.age}")
```

### Named Tuples

```python
from typing import NamedTuple


class Point(NamedTuple):
    """Immutable 2D point."""

    x: float
    y: float

    def distance(self, other: "Point") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
```

## Decorators

### Function Decorators

```python
import functools
import time


def timer(func: Callable) -> Callable:
    """Decorator to time function execution."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"{func.__name__} took {elapsed:.4f}s")
        return result

    return wrapper
```

### Parameterized Decorators

```python
def repeat(times: int):
    """Decorator to repeat a function multiple times."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            results = []
            for _ in range(times):
                results.append(func(*args, **kwargs))
            return results

        return wrapper

    return decorator
```

## Concurrency Patterns

### Threading for I/O-bound Tasks

```python
import concurrent.futures


def fetch_url(url: str) -> str:
    import urllib.request

    with urllib.request.urlopen(url) as response:
        return response.read().decode()


def fetch_all_urls(urls: list[str]) -> dict[str, str]:
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(fetch_url, url): url for url in urls}
        # ... logic to gather results
```

### Async/Await for Concurrent I/O

```python
import asyncio


async def fetch_async(url: str) -> str:
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.text()
```

## Memory and Performance

### Memory Optimization with `__slots__`

```python
# Good: __slots__ reduces memory usage
class Point:
    __slots__ = ["x", "y"]

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
```

### String Building Performance

```python
# Bad: O(n²) due to string immutability
result = ""
for item in items:
    result += str(item)

# Good: O(n) using join
result = "".join(str(item) for item in items)
```

## Quick Reference: Python Idioms

| Idiom              | Description                                   |
| ------------------ | --------------------------------------------- |
| EAFP               | Easier to ask for forgiveness than permission |
| Context Manager    | Use`with` for resource management           |
| List Comprehension | For simple transformations                    |
| Generators         | For lazy evaluation and large datasets        |
| Type Hinting       | Annotate function signatures                  |
| Data Classes       | For data containers with generated methods    |
| `__slots__`      | For memory optimization                       |
| f-strings          | For string formatting (Python 3.6+)           |
| `pathlib.Path`   | For path operations                           |
| `enumerate`      | For index-element pairs in loops              |

## Anti-Patterns to Avoid

```python
# Bad: Mutable default arguments
def append_to(item, items=[]): ...


# Good: Use None
def append_to(item, items=None):
    if items is None:
        items = []
    ...


# Bad: Using == None
if value == None:
    ...

# Good: Use 'is None'
if value is None:
    ...

# Bad: Bare except
try:
    risky_operation()
except:
    pass

# Good: Specific exception
try:
    risky_operation()
except SpecificError as e:
    logger.error(...)
```

**Remember**: Python code should be readable, explicit, and follow the principle of least astonishment. When in doubt, prefer clarity over cleverness.