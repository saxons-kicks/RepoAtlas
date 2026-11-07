"""Deterministic, explainable resource classification."""

from __future__ import annotations

import re
from collections.abc import Iterable

CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("ai-agents", (
        "ia & agentes", "ia e agentes", "agentes", "llm", "ai agent", "agentic",
        "mcp", "models", "language model", "rag", "prompt engineering", "copilot",
    )),
    ("qa-testing", (
        "qa", "quality assurance", "qualidade", "testes", "testing", "cypress",
        "appium", "selenium", "jmeter", "playwright", "test automation", "unit test",
        "integration test", "e2e",
    )),
    ("security-osint", (
        "segurança", "seguranca", "osint", "pentest", "security", "bug bounty",
        "vulnerability", "audit", "threat modeling", "exploit",
    )),
    ("game-porting-re", (
        "porting", "porting & re", "engenharia reversa", "reverse engineering",
        "recompila", "ghidra", "x64dbg", "modding", "decompilation", "binary analysis",
    )),
    ("gaming-emulation", (
        "games", "jogos", "gaming", "game", "emulator", "emulation", "playstation",
        "ps2", "ps3", "ps4", "ps5", "bloodborne", "pcsx2", "shadps4",
    )),
    ("automation-web", (
        "automation", "automação", "automacao", "browser", "web scraping", "scraping",
        "scraper", "crawler", "headless", "web automation", "userscript",
    )),
    ("devops-infra", (
        "devops", "infra", "azure devops", "ci/cd", "pipeline", "docker",
        "kubernetes", "deployment", "observability",
    )),
    ("android-mobile", (
        "android", "mobile", "apk", "react native", "flutter", "android app",
    )),
    ("data-finance", (
        "finanças", "financas", "trading", "finance", "dados", "data science",
        "quant", "stock", "market data", "backtesting",
    )),
    ("media-creative", (
        "video", "vídeo", "imagem", "image", "audio", "voice", "music", "media",
        "photo", "editor", "design", "creative", "text to speech", "speech synthesis",
    )),
    ("developer-tools", (
        "ferramentas", "utilitários", "utilitarios", "developer tools", "ides",
        "terminal", "windows tooling", "debugger", "cli", "sdk", "api client",
    )),
    ("learning", (
        "estudos", "aprendizado", "cursos", "documentação", "documentacao",
        "books", "tutorial", "beginners", "course",
    )),
]

CATEGORY_LABELS = {
    "ai-agents": "IA & Agentes",
    "qa-testing": "QA & Testes",
    "security-osint": "Segurança & OSINT",
    "game-porting-re": "Game Porting & Reverse Engineering",
    "gaming-emulation": "Games & Emulação",
    "automation-web": "Automação & Web",
    "devops-infra": "DevOps & Infraestrutura",
    "android-mobile": "Android & Mobile",
    "data-finance": "Dados & Finanças",
    "media-creative": "Mídia & Criação",
    "developer-tools": "Ferramentas de Desenvolvimento",
    "learning": "Estudos & Documentação",
    "other": "Outros",
}


def _norm(text: str) -> str:
    text = text.casefold()
    text = re.sub(r"[^\w\s&/+.-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def classify(
    paths: Iterable[list[str]],
    title: str = "",
    description: str = "",
    topics: Iterable[str] = (),
    language: str = "",
    full_name: str = "",
) -> tuple[list[str], list[str]]:
    """Return up to four matching categories and the first reason for each."""
    path_text = " / ".join(part for path in paths for part in path)
    text = _norm(" ".join([path_text, title, description, " ".join(topics), language, full_name]))
    matches: list[str] = []
    reasons: list[str] = []
    for key, terms in CATEGORY_RULES:
        found = next((term for term in terms if _norm(term) in text), None)
        if found:
            matches.append(key)
            reasons.append(f"termo: {found}")
    if not matches:
        return ["other"], ["sem regra específica correspondente"]
    return matches[:4], reasons[:4]


def build_tags(categories: Iterable[str], topics: Iterable[str], language: str | None, is_fork: bool, archived: bool) -> list[str]:
    """Create stable, filter-friendly tags without assigning a quality score."""
    tags = {str(topic).strip().casefold() for topic in topics if str(topic).strip()}
    tags.update(f"category:{category}" for category in categories)
    if language:
        tags.add(f"language:{language.casefold()}")
    if is_fork:
        tags.add("fork")
    if archived:
        tags.add("archived")
    return sorted(tags)
