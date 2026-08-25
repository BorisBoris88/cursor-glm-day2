import random
from string.templatelib import Interpolation, Template, convert
from rich.console import Console

HACKER_ALIASES_HEADER = "Фейковые хакерские алиасы:"
ALIAS_PREFIX = " --- "
ALIAS_SUFFIX = " ---"


def render(template: Template) -> str:
    parts = []
    for item in template:
        match item:
            case str(s):
                parts.append(s)
            case Interpolation(value, _, conversion, format_spec):
                parts.append(format(convert(value, conversion), format_spec))
    return "".join(parts)


def uppercase(template: Template) -> Template:
    pieces = []
    for item in template:
        if isinstance(item, str):
            pieces.append(item)
        else:
            text = format(convert(item.value, item.conversion), item.format_spec)
            pieces.append(Interpolation(text.upper(), item.expression, None, ""))
    return Template(*pieces)


def header_line(header: str) -> Template:
    return t"{header}"


def alias_line(alias: str) -> Template:
    return Template(
        ALIAS_PREFIX,
        Interpolation(alias, "alias", None, ""),
        ALIAS_SUFFIX,
    )

def generate_hacker_aliases(n: int = 5) -> list[str]:
    """Генерирует уникальные фейковые хакерские алиасы."""
    prefixes = [
        "Neo", "Shadow", "Ghost", "Crypt", "Zero", "Dark", "Silent", "Phantom", "Byte", "Nano",
        "Cyber", "Plasma", "Razor", "Omega", "Vortex", "Glitch", "Pulse", "Cipher", "Nova", "Root",
    ]
    suffixes = [
        "Cipher", "Blade", "Runner", "Hacker", "Blast", "Storm", "Phreak", "Wraith", "Flux", "Hex",
        "Ghost", "Node", "Shift", "Craft", "X", "Trace", "Scope", "Whisper", "Strike",
    ]
    max_unique = len(prefixes) * len(suffixes)
    count = max(1, min(n, max_unique))
    aliases: set[str] = set()
    while len(aliases) < count:
        alias = random.choice(prefixes) + random.choice(suffixes)
        aliases.add(alias)
    return list(aliases)


def main() -> None:
    """CLI: печатает алиасы и пишет снимок в data.json."""
    import json

    console = Console()
    t_aliases = generate_hacker_aliases()
    console.print(render(uppercase(header_line(HACKER_ALIASES_HEADER))), style="bold red")
    for t_alias in t_aliases:
        console.print(render(uppercase(alias_line(t_alias))), style="bold cyan")
    with open("data.json", "w", encoding="utf-8") as handle:
        json.dump({"aliases": t_aliases}, handle, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()