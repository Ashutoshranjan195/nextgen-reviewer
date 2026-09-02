"""
Rule-Based Code Review Engine

A self-contained reviewer that uses regex pattern matching to detect issues
across multiple programming languages. It also incorporates user-uploaded
CSV rules into the review process.

No external API key or LLM service is required.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Allowed issue types — anything else maps to "other"
VALID_ISSUE_TYPES = {
    "formatting", "performance", "security",
    "best-practice", "optimization", "other",
}


@dataclass
class ReviewResult:
    """Structured result from the code review engine."""
    rating: int
    feedback: str
    issues: List[Dict[str, str]] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
#  Built-in Rule Definitions
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PatternRule:
    """A single regex-based code quality rule."""
    pattern: str
    flags: int
    issue_type: str
    description: str
    languages: Optional[set] = None  # None = applies to all languages


# Rules that apply to ALL languages
UNIVERSAL_RULES: List[PatternRule] = [
    # ── Formatting ────────────────────────────────────────────────────────
    PatternRule(
        pattern=r"^.{121,}$",
        flags=re.MULTILINE,
        issue_type="formatting",
        description="Line exceeds 120 characters. Consider wrapping long lines for readability.",
    ),
    PatternRule(
        pattern=r"\t",
        flags=0,
        issue_type="formatting",
        description="Tab characters detected. Use consistent indentation (prefer spaces).",
    ),
    PatternRule(
        pattern=r"[ \t]+$",
        flags=re.MULTILINE,
        issue_type="formatting",
        description="Trailing whitespace detected. Remove trailing spaces/tabs.",
    ),

    # ── Security ──────────────────────────────────────────────────────────
    PatternRule(
        pattern=r"""(?:password|passwd|secret|api_key|apikey|token|auth_token|private_key)\s*=\s*['"][^'"]{3,}['"]""",
        flags=re.IGNORECASE,
        issue_type="security",
        description="Possible hardcoded secret or credential detected. Use environment variables or a secrets manager instead.",
    ),
    PatternRule(
        pattern=r"""(?:password|passwd|secret|api_key|apikey|token|auth_token|private_key)\s*=\s*['\"][^'\"]{3,}['\"]""",
        flags=re.IGNORECASE,
        issue_type="security",
        description="Possible hardcoded secret or credential detected. Use environment variables or a secrets manager instead.",
    ),
    PatternRule(
        pattern=r"https?://[^\s]*(?:password|token|key|secret)=[^\s&]+",
        flags=re.IGNORECASE,
        issue_type="security",
        description="URL with embedded credentials detected. Never put secrets in URLs.",
    ),

    # ── Best Practice ─────────────────────────────────────────────────────
    PatternRule(
        pattern=r"\b(?:TODO|FIXME|HACK|XXX|WORKAROUND)\b",
        flags=re.IGNORECASE,
        issue_type="best-practice",
        description="Unresolved TODO/FIXME/HACK comment found. Address these before production.",
    ),
    PatternRule(
        pattern=r"(?:^|\n)\s*(?://|#|/\*)\s*(?:debug|test|remove|delete|temporary|temp)\b",
        flags=re.IGNORECASE | re.MULTILINE,
        issue_type="best-practice",
        description="Debug/temporary comment found. Clean up before committing.",
    ),

    # ── Formatting / Naming ───────────────────────────────────────────────
    PatternRule(
        pattern=r"(?<!\w)[a-z]\s*=\s*(?!.*(?:for|in|range|enumerate|zip|map|filter|lambda|import))",
        flags=0,
        issue_type="formatting",
        description="Single-character variable name detected. Use descriptive names for better readability.",
        languages={"python", "javascript", "typescript", "java", "c++", "c#", "ruby", "php", "rust"},
    ),
]


# Language-specific rules
LANGUAGE_RULES: Dict[str, List[PatternRule]] = {
    "python": [
        PatternRule(
            pattern=r"except\s*:\s*\n\s*(?:pass|\.\.\.)\s*(?:\n|$)",
            flags=0,
            issue_type="best-practice",
            description="Bare except with pass/... found. Avoid silently swallowing exceptions; log or handle them.",
        ),
        PatternRule(
            pattern=r"except\s+Exception\s*(?:as\s+\w+)?\s*:\s*\n\s*(?:pass|\.\.\.)\s*(?:\n|$)",
            flags=0,
            issue_type="best-practice",
            description="Catching broad Exception and ignoring it. Be specific about exception types.",
        ),
        PatternRule(
            pattern=r"\beval\s*\(",
            flags=0,
            issue_type="security",
            description="Use of eval() is dangerous. It can execute arbitrary code — use ast.literal_eval() or safer alternatives.",
        ),
        PatternRule(
            pattern=r"\bexec\s*\(",
            flags=0,
            issue_type="security",
            description="Use of exec() is a security risk. Avoid executing dynamic code strings.",
        ),
        PatternRule(
            pattern=r"import\s+\*",
            flags=0,
            issue_type="best-practice",
            description="Wildcard import (import *) pollutes the namespace. Import specific names instead.",
        ),
        PatternRule(
            pattern=r"print\s*\(",
            flags=0,
            issue_type="best-practice",
            description="print() statements found. Use the logging module for production code.",
        ),
        PatternRule(
            pattern=r"\bdef\s+\w+\([^)]*\)\s*:",
            flags=0,
            issue_type="optimization",
            description="Function definition without type hints. Consider adding type annotations for better code documentation.",
        ),
        PatternRule(
            pattern=r"(?:for\s+\w+\s+in\s+range\s*\(\s*len\s*\()",
            flags=0,
            issue_type="optimization",
            description="Using range(len(...)) is unpythonic. Use enumerate() or iterate directly over the collection.",
        ),
        PatternRule(
            pattern=r"\bos\.system\s*\(",
            flags=0,
            issue_type="security",
            description="os.system() is vulnerable to shell injection. Use subprocess.run() with a list of arguments.",
        ),
        PatternRule(
            pattern=r"\.format\s*\(|%\s*\(",
            flags=0,
            issue_type="optimization",
            description="Consider using f-strings (Python 3.6+) for cleaner string formatting.",
        ),
        PatternRule(
            pattern=r"\[\s*\w+\s+for\s+\w+\s+in\s+.*\s+if\s+.*\s+for\s+",
            flags=0,
            issue_type="formatting",
            description="Nested list comprehension detected. Consider refactoring into explicit loops for clarity.",
        ),
    ],

    "javascript": [
        PatternRule(
            pattern=r"\bconsole\.\w+\s*\(",
            flags=0,
            issue_type="best-practice",
            description="console.log/warn/error statements found. Remove or replace with a proper logging framework.",
        ),
        PatternRule(
            pattern=r"\bvar\s+",
            flags=0,
            issue_type="best-practice",
            description="Use of 'var' detected. Prefer 'const' or 'let' for block-scoped variables.",
        ),
        PatternRule(
            pattern=r"==(?!=)",
            flags=0,
            issue_type="best-practice",
            description="Loose equality (==) used. Prefer strict equality (===) to avoid type coercion bugs.",
        ),
        PatternRule(
            pattern=r"!=(?!=)",
            flags=0,
            issue_type="best-practice",
            description="Loose inequality (!=) used. Prefer strict inequality (!==).",
        ),
        PatternRule(
            pattern=r"\beval\s*\(",
            flags=0,
            issue_type="security",
            description="eval() is a serious security risk. It can execute arbitrary code.",
        ),
        PatternRule(
            pattern=r"innerHTML\s*=",
            flags=0,
            issue_type="security",
            description="Direct innerHTML assignment can lead to XSS vulnerabilities. Use textContent or sanitize input.",
        ),
        PatternRule(
            pattern=r"document\.write\s*\(",
            flags=0,
            issue_type="security",
            description="document.write() can overwrite the entire document and is an XSS risk. Use DOM manipulation instead.",
        ),
        PatternRule(
            pattern=r"new\s+Promise\s*\(\s*(?:async\s+)?(?:function|\()",
            flags=0,
            issue_type="optimization",
            description="Avoid the Promise constructor anti-pattern. Use async/await directly when possible.",
        ),
        PatternRule(
            pattern=r"setTimeout\s*\(\s*['\"]",
            flags=0,
            issue_type="security",
            description="Passing a string to setTimeout is equivalent to eval(). Pass a function reference instead.",
        ),
    ],

    "typescript": [
        PatternRule(
            pattern=r"\bconsole\.\w+\s*\(",
            flags=0,
            issue_type="best-practice",
            description="console.log/warn/error statements found. Remove or replace with a proper logging framework.",
        ),
        PatternRule(
            pattern=r":\s*any\b",
            flags=0,
            issue_type="best-practice",
            description="Use of 'any' type defeats TypeScript's type safety. Use specific types or generics.",
        ),
        PatternRule(
            pattern=r"@ts-ignore",
            flags=0,
            issue_type="best-practice",
            description="@ts-ignore suppresses TypeScript errors. Fix the underlying type issue instead.",
        ),
        PatternRule(
            pattern=r"as\s+any\b",
            flags=0,
            issue_type="best-practice",
            description="Casting to 'any' bypasses type checking. Use proper type narrowing or generics.",
        ),
        PatternRule(
            pattern=r"\bvar\s+",
            flags=0,
            issue_type="best-practice",
            description="Use of 'var' detected. Prefer 'const' or 'let' for block-scoped variables.",
        ),
        PatternRule(
            pattern=r"==(?!=)",
            flags=0,
            issue_type="best-practice",
            description="Loose equality (==) used. Prefer strict equality (===).",
        ),
        PatternRule(
            pattern=r"\beval\s*\(",
            flags=0,
            issue_type="security",
            description="eval() is a serious security risk in TypeScript/JavaScript.",
        ),
    ],

    "java": [
        PatternRule(
            pattern=r"System\.out\.print",
            flags=0,
            issue_type="best-practice",
            description="System.out.println found. Use a logging framework (SLF4J, Log4j) in production code.",
        ),
        PatternRule(
            pattern=r"e\.printStackTrace\s*\(",
            flags=0,
            issue_type="best-practice",
            description="printStackTrace() sends to stderr. Use a logger to capture stack traces.",
        ),
        PatternRule(
            pattern=r"catch\s*\(\s*Exception\s+",
            flags=0,
            issue_type="best-practice",
            description="Catching generic Exception. Be specific about exception types to handle errors properly.",
        ),
        PatternRule(
            pattern=r"public\s+\w+\s+\w+\s*;",
            flags=0,
            issue_type="best-practice",
            description="Public field without encapsulation. Use private fields with getters/setters.",
        ),
        PatternRule(
            pattern=r"new\s+String\s*\(",
            flags=0,
            issue_type="performance",
            description="Unnecessary String object creation. Use string literals directly.",
        ),
        PatternRule(
            pattern=r"\bString\s+\w+\s*=\s*\"\";\s*\n(?:.*\+=)",
            flags=re.MULTILINE,
            issue_type="performance",
            description="String concatenation in a loop. Use StringBuilder for better performance.",
        ),
        PatternRule(
            pattern=r"synchronized\s*\(",
            flags=0,
            issue_type="performance",
            description="synchronized block detected. Verify that this is necessary and consider using java.util.concurrent utilities.",
        ),
    ],

    "go": [
        PatternRule(
            pattern=r"fmt\.Print",
            flags=0,
            issue_type="best-practice",
            description="fmt.Print/Println used. Consider using the log package or a structured logger for production.",
        ),
        PatternRule(
            pattern=r"panic\s*\(",
            flags=0,
            issue_type="best-practice",
            description="panic() found. Prefer returning errors instead of panicking in library code.",
        ),
        PatternRule(
            pattern=r"\b_\s*=\s*\w+\.\w+\(",
            flags=0,
            issue_type="best-practice",
            description="Error return value explicitly ignored with _. Check and handle errors properly.",
        ),
        PatternRule(
            pattern=r"interface\s*\{\s*\}",
            flags=0,
            issue_type="best-practice",
            description="Empty interface (interface{}) detected. Use 'any' (Go 1.18+) or define specific interfaces.",
        ),
        PatternRule(
            pattern=r"\bos\.Exit\s*\(",
            flags=0,
            issue_type="best-practice",
            description="os.Exit() prevents deferred functions from running. Return from main() instead.",
        ),
    ],

    "rust": [
        PatternRule(
            pattern=r"\bunwrap\s*\(",
            flags=0,
            issue_type="best-practice",
            description="unwrap() will panic on None/Err. Use pattern matching, '?', or unwrap_or/unwrap_or_else.",
        ),
        PatternRule(
            pattern=r"\bexpect\s*\(",
            flags=0,
            issue_type="best-practice",
            description="expect() will panic with a message. Consider proper error handling with '?' operator.",
        ),
        PatternRule(
            pattern=r"\bunsafe\s*\{",
            flags=0,
            issue_type="security",
            description="unsafe block detected. Minimize unsafe code and document safety invariants.",
        ),
        PatternRule(
            pattern=r"\.clone\s*\(",
            flags=0,
            issue_type="performance",
            description="clone() call detected. Consider whether borrowing or references would avoid unnecessary copies.",
        ),
        PatternRule(
            pattern=r"println!\s*\(",
            flags=0,
            issue_type="best-practice",
            description="println!() found. Use a logging crate (log, tracing) for production applications.",
        ),
    ],

    "c++": [
        PatternRule(
            pattern=r"\bnew\s+\w+",
            flags=0,
            issue_type="best-practice",
            description="Raw 'new' detected. Prefer smart pointers (std::unique_ptr, std::shared_ptr) for memory safety.",
        ),
        PatternRule(
            pattern=r"\bdelete\s+",
            flags=0,
            issue_type="best-practice",
            description="Manual 'delete' detected. Use RAII and smart pointers to manage memory automatically.",
        ),
        PatternRule(
            pattern=r"\busing\s+namespace\s+std\s*;",
            flags=0,
            issue_type="best-practice",
            description="'using namespace std' pollutes the global namespace. Use specific std:: qualifiers.",
        ),
        PatternRule(
            pattern=r"\bmalloc\s*\(",
            flags=0,
            issue_type="best-practice",
            description="C-style malloc() in C++ code. Use new/make_unique/make_shared instead.",
        ),
        PatternRule(
            pattern=r"\bprintf\s*\(",
            flags=0,
            issue_type="best-practice",
            description="C-style printf() in C++ code. Prefer std::cout or a formatting library (fmt/std::format).",
        ),
        PatternRule(
            pattern=r"#define\s+\w+\s+\w+",
            flags=0,
            issue_type="best-practice",
            description="Preprocessor macro define detected. Prefer constexpr/const variables or inline functions.",
        ),
    ],

    "c#": [
        PatternRule(
            pattern=r"Console\.Write",
            flags=0,
            issue_type="best-practice",
            description="Console.Write/WriteLine found. Use ILogger or a logging framework in production.",
        ),
        PatternRule(
            pattern=r"catch\s*\(\s*Exception\s+",
            flags=0,
            issue_type="best-practice",
            description="Catching generic Exception. Catch specific exception types for better error handling.",
        ),
        PatternRule(
            pattern=r"\.Result\b",
            flags=0,
            issue_type="performance",
            description="Synchronous .Result on async task can cause deadlocks. Use 'await' instead.",
        ),
        PatternRule(
            pattern=r"\.Wait\s*\(",
            flags=0,
            issue_type="performance",
            description="Synchronous .Wait() on async task can cause deadlocks. Use 'await' instead.",
        ),
        PatternRule(
            pattern=r"string\s+\w+\s*=\s*\"\";\s*\n(?:.*\+=)",
            flags=re.MULTILINE,
            issue_type="performance",
            description="String concatenation detected. Use StringBuilder for repeated concatenation.",
        ),
    ],

    "ruby": [
        PatternRule(
            pattern=r"\bputs\s+",
            flags=0,
            issue_type="best-practice",
            description="puts statement found. Use the Logger class for structured logging in production.",
        ),
        PatternRule(
            pattern=r"\beval\s*\(",
            flags=0,
            issue_type="security",
            description="eval() is a security risk. Avoid evaluating dynamic strings.",
        ),
        PatternRule(
            pattern=r"rescue\s*\n\s*(?:nil|retry)\s*\n",
            flags=0,
            issue_type="best-practice",
            description="Empty rescue block found. Handle or log exceptions instead of silencing them.",
        ),
        PatternRule(
            pattern=r"rescue\s+Exception\b",
            flags=0,
            issue_type="best-practice",
            description="Rescuing Exception catches too broadly (including SystemExit, SignalException). Rescue StandardError instead.",
        ),
        PatternRule(
            pattern=r"\bsystem\s*\(",
            flags=0,
            issue_type="security",
            description="system() call detected. Use Open3 or individual exec methods to avoid shell injection.",
        ),
    ],

    "php": [
        PatternRule(
            pattern=r"\beval\s*\(",
            flags=0,
            issue_type="security",
            description="eval() is extremely dangerous in PHP. It can execute arbitrary code from user input.",
        ),
        PatternRule(
            pattern=r"\$_(?:GET|POST|REQUEST|COOKIE)\b",
            flags=0,
            issue_type="security",
            description="Direct use of superglobals ($_GET, $_POST, etc.) without validation. Sanitize and validate all user input.",
        ),
        PatternRule(
            pattern=r"\becho\s+",
            flags=0,
            issue_type="security",
            description="echo statement without escaping. Use htmlspecialchars() to prevent XSS when outputting user data.",
        ),
        PatternRule(
            pattern=r"mysql_\w+\s*\(",
            flags=0,
            issue_type="security",
            description="Deprecated mysql_* functions detected. Use PDO or mysqli with prepared statements.",
        ),
        PatternRule(
            pattern=r"\bdie\s*\(",
            flags=0,
            issue_type="best-practice",
            description="die() halts execution abruptly. Use proper exception handling and error responses.",
        ),
        PatternRule(
            pattern=r"\bvar_dump\s*\(",
            flags=0,
            issue_type="best-practice",
            description="var_dump() found. Remove debug output before production deployment.",
        ),
        PatternRule(
            pattern=r"\bshell_exec\s*\(",
            flags=0,
            issue_type="security",
            description="shell_exec() is a command injection risk. Use escapeshellarg()/escapeshellcmd() and validate input.",
        ),
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
#  CSV Rule Integration
# ─────────────────────────────────────────────────────────────────────────────

def _apply_csv_rules(
    code: str,
    csv_rules: List[Dict[str, str]],
) -> List[Dict[str, str]]:
    """
    Apply user-uploaded CSV rules as keyword-based checks.

    Each CSV rule has a 'type' and 'description'. We search the code for
    keywords extracted from the description to see if the rule is relevant.
    """
    issues: List[Dict[str, str]] = []

    for rule in csv_rules:
        rule_type = rule.get("type", "other").strip().lower()
        description = rule.get("description", "").strip()

        if not description:
            continue

        # Normalize the type to valid set
        if rule_type not in VALID_ISSUE_TYPES:
            rule_type = "other"

        # Extract meaningful keywords from the description (3+ chars)
        words = re.findall(r"\b[a-zA-Z_]{3,}\b", description.lower())
        # Filter out very common words
        stopwords = {
            "the", "and", "for", "are", "but", "not", "you", "all",
            "can", "had", "her", "was", "one", "our", "out", "use",
            "has", "have", "with", "this", "that", "from", "they",
            "been", "said", "each", "which", "their", "will", "other",
            "about", "make", "should", "avoid", "using", "instead",
            "code", "when", "ensure", "always", "never", "must",
        }
        keywords = [w for w in words if w not in stopwords]

        if not keywords:
            # If no useful keywords, flag the rule unconditionally
            issues.append({
                "type": rule_type,
                "description": f"[Custom Rule] {description}",
            })
            continue

        # Check if any keyword appears in the code (case-insensitive)
        code_lower = code.lower()
        matched = any(kw in code_lower for kw in keywords)

        if matched:
            issues.append({
                "type": rule_type,
                "description": f"[Custom Rule] {description}",
            })

    return issues


# ─────────────────────────────────────────────────────────────────────────────
#  Core Analysis Engine
# ─────────────────────────────────────────────────────────────────────────────

def _run_builtin_rules(code: str, language: str) -> List[Dict[str, str]]:
    """Run all applicable built-in regex rules against the code."""
    issues: List[Dict[str, str]] = []
    seen_descriptions: set = set()  # De-duplicate

    lang_key = language.lower().strip()

    # Gather applicable rules
    applicable_rules: List[PatternRule] = []

    # Universal rules (check language filter)
    for rule in UNIVERSAL_RULES:
        if rule.languages is None or lang_key in rule.languages:
            applicable_rules.append(rule)

    # Language-specific rules
    if lang_key in LANGUAGE_RULES:
        applicable_rules.extend(LANGUAGE_RULES[lang_key])

    # Run each rule
    for rule in applicable_rules:
        try:
            if re.search(rule.pattern, code, rule.flags):
                if rule.description not in seen_descriptions:
                    seen_descriptions.add(rule.description)
                    issues.append({
                        "type": rule.issue_type,
                        "description": rule.description,
                    })
        except re.error as e:
            logger.warning("Regex error in rule '%s': %s", rule.description[:50], e)

    return issues


def _check_structural_issues(code: str, language: str) -> List[Dict[str, str]]:
    """Check for structural / complexity issues beyond simple regex."""
    issues: List[Dict[str, str]] = []
    lines = code.split("\n")
    total_lines = len(lines)

    # Very long file
    if total_lines > 500:
        issues.append({
            "type": "best-practice",
            "description": f"File is {total_lines} lines long. Consider breaking it into smaller, focused modules.",
        })

    # Deep nesting detection (rough heuristic)
    max_indent = 0
    for line in lines:
        if line.strip():
            indent = len(line) - len(line.lstrip())
            # Normalize: 2 spaces or 4 spaces or 1 tab = 1 level
            level = indent // 2 if indent < 20 else indent // 4
            max_indent = max(max_indent, level)

    if max_indent >= 6:
        issues.append({
            "type": "optimization",
            "description": f"Deeply nested code detected (≈{max_indent} levels). Refactor using early returns, guard clauses, or extract methods.",
        })

    # Functions/methods that are too long
    lang_lower = language.lower()
    if lang_lower in ("python",):
        func_pattern = re.compile(r"^\s*def\s+\w+", re.MULTILINE)
    elif lang_lower in ("javascript", "typescript"):
        func_pattern = re.compile(r"(?:function\s+\w+|(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)|[^=])\s*=>)", re.MULTILINE)
    elif lang_lower in ("java", "c#", "c++"):
        func_pattern = re.compile(r"(?:public|private|protected|static|void|int|string|bool)\s+\w+\s*\([^)]*\)\s*\{", re.MULTILINE)
    else:
        func_pattern = None

    if func_pattern:
        func_starts = [m.start() for m in func_pattern.finditer(code)]
        if len(func_starts) > 0:
            for i, start in enumerate(func_starts):
                end = func_starts[i + 1] if i + 1 < len(func_starts) else len(code)
                func_body = code[start:end]
                func_lines = func_body.count("\n")
                if func_lines > 80:
                    issues.append({
                        "type": "optimization",
                        "description": f"Long function/method detected (~{func_lines} lines). Break it into smaller, single-responsibility functions.",
                    })
                    break  # Report once

    # Empty file / trivially short
    non_empty_lines = sum(1 for line in lines if line.strip())
    if non_empty_lines < 2:
        issues.append({
            "type": "other",
            "description": "Code is trivially short. This may be a snippet rather than a complete implementation.",
        })

    # Duplicate consecutive lines (copy-paste smell)
    for i in range(1, len(lines)):
        if lines[i].strip() and lines[i].strip() == lines[i - 1].strip() and len(lines[i].strip()) > 10:
            issues.append({
                "type": "optimization",
                "description": "Duplicate consecutive lines detected. This may indicate copy-paste errors.",
            })
            break

    return issues


# ─────────────────────────────────────────────────────────────────────────────
#  Rating & Feedback Generation
# ─────────────────────────────────────────────────────────────────────────────

def _calculate_rating(issues: List[Dict[str, str]], code: str) -> int:
    """
    Calculate a quality rating from 1–10.
    Starts at 10 and deducts points per issue, weighted by severity.
    """
    severity_weight = {
        "security": 1.5,
        "performance": 1.0,
        "best-practice": 0.7,
        "optimization": 0.6,
        "formatting": 0.4,
        "other": 0.5,
    }

    deduction = 0.0
    for issue in issues:
        weight = severity_weight.get(issue.get("type", "other"), 0.5)
        deduction += weight

    # Cap the deduction so the rating doesn't go below 1
    rating = max(1, min(10, round(10 - deduction)))

    # Bonus: if code is non-trivial (>10 lines) and has very few issues
    lines = code.split("\n")
    non_empty = sum(1 for l in lines if l.strip())
    if non_empty > 10 and len(issues) <= 1:
        rating = min(10, rating + 1)

    return rating


def _generate_feedback(
    rating: int,
    issues: List[Dict[str, str]],
    language: str,
    code: str,
) -> str:
    """Generate human-readable overall feedback based on the review results."""
    lines = code.split("\n")
    total_lines = len(lines)
    issue_count = len(issues)

    # Count issue types
    type_counts: Dict[str, int] = {}
    for issue in issues:
        t = issue.get("type", "other")
        type_counts[t] = type_counts.get(t, 0) + 1

    # Rating category
    if rating >= 9:
        quality = "Excellent"
        opening = f"Excellent {language} code! Very clean and well-structured."
    elif rating >= 7:
        quality = "Good"
        opening = f"Good {language} code overall with minor areas for improvement."
    elif rating >= 5:
        quality = "Fair"
        opening = f"Fair {language} code — several issues were identified that should be addressed."
    elif rating >= 3:
        quality = "Needs Improvement"
        opening = f"This {language} code needs significant improvement across multiple areas."
    else:
        quality = "Poor"
        opening = f"This {language} code has critical issues that must be fixed before use."

    # Build detailed feedback
    parts = [opening]

    parts.append(f" Analyzed {total_lines} lines and found {issue_count} issue(s).")

    if "security" in type_counts:
        parts.append(
            f" ⚠️ {type_counts['security']} security issue(s) found — these should be addressed immediately."
        )

    if "performance" in type_counts:
        parts.append(
            f" {type_counts['performance']} performance concern(s) identified."
        )

    if "best-practice" in type_counts:
        parts.append(
            f" {type_counts['best-practice']} best-practice suggestion(s) for cleaner code."
        )

    if "optimization" in type_counts:
        parts.append(
            f" {type_counts['optimization']} optimization opportunity/ies noted."
        )

    if issue_count == 0:
        parts.append(" No issues detected — great job! Consider adding tests and documentation if not already present.")

    return "".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────────────

async def generate_review(
    code: str,
    language: str,
    rules: Optional[List[Dict[str, str]]] = None,
) -> ReviewResult:
    """
    Generate a code review for the given code and language.

    1. Runs built-in regex rules appropriate for the language.
    2. Checks structural / complexity issues.
    3. Applies user-uploaded CSV rules if any.
    4. Calculates a deduction-based rating (1–10).
    5. Generates descriptive feedback.

    Args:
        code: The source code to review.
        language: The programming language.
        rules: Optional list of {"type": str, "description": str} from CSV uploads.

    Returns:
        A ReviewResult with rating, feedback, and issues.
    """
    csv_rules = rules or []

    # Step 1: Run built-in regex rules
    builtin_issues = _run_builtin_rules(code, language)

    # Step 2: Check structural issues
    structural_issues = _check_structural_issues(code, language)

    # Step 3: Apply CSV rules
    csv_issues = _apply_csv_rules(code, csv_rules) if csv_rules else []

    # Step 4: Combine all issues (de-duplicate by description)
    all_issues: List[Dict[str, str]] = []
    seen: set = set()
    for issue in builtin_issues + structural_issues + csv_issues:
        desc = issue["description"]
        if desc not in seen:
            seen.add(desc)
            all_issues.append(issue)

    # Step 5: Calculate rating
    rating = _calculate_rating(all_issues, code)

    # Step 6: Generate feedback
    feedback = _generate_feedback(rating, all_issues, language, code)

    logger.info(
        "Review complete: language=%s, issues=%d, rating=%d",
        language, len(all_issues), rating,
    )

    return ReviewResult(rating=rating, feedback=feedback, issues=all_issues)
