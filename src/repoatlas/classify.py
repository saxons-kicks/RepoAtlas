"""Deterministic, explainable resource classification."""

from __future__ import annotations

import re
from collections.abc import Iterable

CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("ai-agents", ("ia & agentes", "ia e agentes", "agentes", "llm", "ai agent", "agentic", "mcp", "models")),
    ("qa-testing", ("qa", "qualidade", "testes", "testing", "cypress", "appium", "selenium", "jmeter", "playwright")),
    ("game-porting-re", ("porting", "porting & re", "engenharia reversa", "reverse engineering", "recompila", "ghidra", "x64dbg", "modding")),
    ("security-osint", ("segurança", "seguranca", "osint", "pentest", "security", "bug bounty", "vulnerability")),
    ("devops-infra", ("devops", "infra", "azure devops", "ci/cd", "pipeline", "docker", "kubernetes")),
    ("android-mobile", ("android", "mobile", "apk", "react native", "flutter")),
    ("data-finance", ("finanças", "financas", "trading", "finance", "dados", "data science", "quant")),
    ("gaming", ("games", "jogos", "gaming", "game")),
    ("developer-tools", ("ferramentas", "utilitários", "utilitarios", "developer tools", "ides", "terminal", "windows tooling")),
    ("learning", ("estudos", "aprendizado", "cursos", "documentação", "documentacao", "books")),
]
CATEGORY_LABELS = {
    "ai-agents": "IA & Agentes",
    "qa-testing": "QA & Testes",
    "game-porting-re": "Game Porting & Reverse Engineering",
    "security-osint": "Segurança & OSINT",
    "devops-infra": "DevOps & Infraestrutura",
    "android-mobile": "Android & Mobile",
    "data-finance": "Dados & Finanças",
    "gaming": "Games",
    "developer-tools": "Ferramentas de Desenvolvimento",
    "learning": "Estudos & Documentação",
    "other": "Outros",
}


def _norm(text: str) -> str:
    text = text.casefold()
    text = re.sub(r"[^\w\s&/+.-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def classify(paths: Iterable[list[str]], title: str = "", description: str = "", topics: Iterable[str] = ()) -> tuple[list[str], list[str]]:
    path_text = " / ".join(part for path in paths for part in path)
    text = _norm(" ".join([path_text, title, description, " ".join(topics)]))
    matches: list[str] = []
    reasons: list[str] = []
    for key, terms in CATEGORY_RULES:
        found = next((term for term in terms if _norm(term) in text), None)
        if found:
            matches.append(key)
            reasons.append(f"termo: {found}")
    if not matches:
        matches = ["other"]
        reasons = ["sem regra específica correspondente"]
    return matches[:3], reasons[:3]
