---
name: github-markdown-formatting
description: Syntax standards, formatting guidelines, and common error prevention for GitHub Flavored Markdown (GFM) and GitHub-rendered Mermaid diagrams.
---

# GitHub Markdown & Mermaid Syntax Formatting Standard

This skill provides strict guidelines and syntax rules to ensure all generated Markdown content and embedded Mermaid diagrams render cleanly and error-free when rendered on GitHub (Issues, PRs, Discussions, and Repositories).

---

## 1. GitHub Flavored Markdown (GFM) Formatting Rules

### A. Blank Lines Around Block Elements
GitHub's GFM parser strictly requires empty blank lines before and after structural block elements. Missing blank lines cause elements to collapse or render inline.

* **Headings:** Always put a blank line before and after headers (`#`, `##`, `###`).
* **Code Blocks:** Always put a blank line before ` ``` ` and after closing ` ``` `.
* **Lists & Tables:** Ensure an empty line precedes and follows lists, task lists, and markdown tables.
* **Blockquotes & HRs:** Separate blockquotes (`>`) and horizontal rules (`---`) with blank lines.

### B. Header Syntax
* Always include a space between `#` symbols and header text (e.g. `## Section Title`, NOT `##Section Title`).

### C. Code Blocks & Fences
* **Language Tags:** Always specify a language tag (e.g. ```` ```json ````, ```` ```python ````, ```` ```mermaid ````).
* **Fence Closure:** Every opening ` ``` ` must have a matching closing ` ``` ` on its own line. Unclosed code blocks render the rest of the document as raw text.

### D. HTML & Generic Type Escaping
* GitHub sanitizes raw HTML tags. Unescaped placeholders or generic types like `<T>`, `<string>`, `<id>` in plain text will be hidden or corrupted by the HTML sanitizer.
* **Rule:** Always wrap generic types, placeholders, or XML/HTML-like tags in code spans: `` `<T>` `` or `` `<string>` ``.

### E. Markdown Tables
* Include outer pipes for table rows (`| Header 1 | Header 2 |`).
* Header separator row is required (`| --- | --- |`).
* If cell content includes a pipe character `|`, escape it as `\|`.

### F. Task Lists
* Use valid task list syntax: `- [ ] Uncompleted task` and `- [x] Completed task`.
* Ensure a space exists inside `[ ]`.

---

## 2. GitHub Mermaid Diagram Syntax Rules

GitHub renders Mermaid diagrams using client-side rendering. To prevent rendering exceptions ("Syntax error in graph"), adhere strictly to the following rules:

### A. Node Labels & Special Characters
* **Rule:** ALWAYS wrap node label text in double quotes `""` whenever it contains spaces, parentheses `()`, brackets `[]`, braces `{}`, colons `:`, slashes `/`, quotes, or special characters.
* **Correct:** `A["Client App (Web)"] --> B["API Endpoint: /v1/auth"]`
* **Incorrect:** `A[Client App (Web)] --> B[API Endpoint: /v1/auth]` *(Will break renderer due to unquoted parentheses and colons)*

### B. Node Identifier Rules
* Use clean alphanumeric IDs for nodes (e.g. `node1`, `client_app`, `db_primary`).
* **Avoid Reserved Keywords:** NEVER use Mermaid reserved keywords as node IDs. Reserved words include: `end`, `subgraph`, `style`, `class`, `graph`, `flowchart`, `click`, `call`, `default`, `state`.
* **Correct:** `node_end["End of Process"]`
* **Incorrect:** `end["End of Process"]` *(Will break subgraph structure)*

### C. Diagram Types & Headers
* **Flowcharts:** Prefer `flowchart TD` or `flowchart LR` over legacy `graph` syntax.
* **Sequence Diagrams:** Use `sequenceDiagram`. Explicitly declare participants when possible:
  ```mermaid
  sequenceDiagram
      autonumber
      actor User
      participant Gateway as API Gateway
      participant Service as AuthService
      User->>Gateway: POST /login
      Gateway->>Service: Validate credentials
  ```
* **ER Diagrams:** Use `erDiagram`. Ensure relationship syntax uses valid cardinalities (`||--o{`, `||--||`).

### D. Subgraphs
* Always give subgraphs a unique alphanumeric ID and explicit quoted title:
  ```mermaid
  subgraph auth_subsystem ["Authentication Subsystem"]
      node_a["Login Page"]
      node_b["Auth Controller"]
  end
  ```
* Every `subgraph` MUST have a corresponding `end` keyword on its own line.

### E. Arrow & Link Syntax
* Use standard valid arrow forms:
  * Solid link with arrow: `-->`
  * Solid link with label: `-->|Label|` or `-- "Label" -->`
  * Dotted link with arrow: `-.->` or `-. "Label" .->`
  * Thick link with arrow: `==>`
* Do NOT use invalid length extensions like `--->` or invalid label placements.

### F. Line Breaks in Node Text
* To create multi-line text inside a node label, use `\n` inside a double-quoted string:
  ```mermaid
  flowchart TD
      step1["Step 1: Parse Input\nValidate Schema"] --> step2["Step 2: Execute"]
  ```
* Do NOT use raw `<br>` tags without wrapping the label in double quotes.

---

## 3. Pre-Publication Checklist

Before outputting Markdown intended for GitHub issues or PR bodies, verify:

1. [ ] Blank lines exist before and after all headers, lists, code blocks, tables, and blockquotes.
2. [ ] All code fences (` ``` `) are properly closed.
3. [ ] All Mermaid node labels with special characters `() [] {} : /` or spaces are enclosed in double quotes `""`.
4. [ ] All Mermaid `subgraph` blocks end with `end`.
5. [ ] Generic types or tags (like `<T>`, `<Response>`) are wrapped in backticks `` `<T>` ``.
