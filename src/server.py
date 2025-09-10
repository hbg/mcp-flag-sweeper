#!/usr/bin/env python3
import os
import json
from pathlib import Path
from fastmcp import FastMCP
from polyglot_piranha import execute_piranha, PiranhaArguments, Rule, RuleGraph, OutgoingEdges

# -------------------------------------------------------------------
# Global flag storage
# -------------------------------------------------------------------
FLAGS_CACHE = {}

# -------------------------------------------------------------------
# Server metadata (acts like a system prompt for MCP clients/agents)
# -------------------------------------------------------------------
app = FastMCP(
    name="piranha-mcp",
    instructions=(
        "An MCP server that integrates with Polyglot Piranha. "
        "It is designed to automatically clean up stale feature flags, "
        "simplify conditional logic, and remove dead branches from code. "
        "Use this server whenever you detect code with feature flag checks "
        "or conditional branches that depend on flags (e.g. "
        "client.GetString(\"flag\") in Go or isFeatureEnabled(\"flag\") in Java). "
        "The tools here transform source code safely by applying Piranha’s "
        "semantics-aware rewrites."
    )
)

# -------------------------------------------------------------------
# Tool: Apply Rewrite
# -------------------------------------------------------------------
@app.tool
def apply_rewrite(code: str, language: str, rules: list[dict] = None, edges: list[dict] = None, flag_name: str = None) -> dict:
    """
    Apply Piranha transformations to a code snippet.

    This tool rewrites code using Polyglot Piranha. It is especially useful
    for removing stale feature flag checks, simplifying conditional logic,
    and cleaning up unused code branches.

    Args:
        code: The source code snippet to transform.
        language: Programming language (e.g. "java", "go").
        rules: A list of Piranha rule definitions (optional, auto-generated if flag_name provided).
        edges: A list of rule graph edges (optional).
        flag_name: Name of flag to clean up (uses cached flag information).
    Returns:
        A dictionary with the transformed code under 'transformed_code'.
    """
    global FLAGS_CACHE

    try:
        # If flag_name is provided, generate rules from cached flag information
        if flag_name and FLAGS_CACHE.get("flags") and flag_name in FLAGS_CACHE["flags"]:
            flag_info = FLAGS_CACHE["flags"][flag_name]
            rules = generate_rules_for_flag(flag_name, flag_info, language)
            edges = []
        elif flag_name:
            # If flag_name is provided but cache is empty, try to load flags first
            try:
                # Try to find flags.json in the current working directory or project root
                working_dir = os.getcwd()
                flags_file = Path(working_dir) / "flags.json"
                if not flags_file.exists():
                    # Try parent directory
                    flags_file = Path(working_dir).parent / "flags.json"
                if not flags_file.exists():
                    # Try the project directory
                    flags_file = Path("/Users/harrisbeg/Desktop/Work/Projects/mcp-piranha") / "flags.json"
                if flags_file.exists():
                    with open(flags_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    parsed_data = parse_flags_json(content)
                    FLAGS_CACHE = {
                        "flags": parsed_data["flags"],
                        "global_patterns": parsed_data["global_patterns"]
                    }
                    if flag_name in FLAGS_CACHE["flags"]:
                        flag_info = FLAGS_CACHE["flags"][flag_name]
                        rules = generate_rules_for_flag(flag_name, flag_info, language)
                        edges = []
                        return {"debug": f"Loaded flag {flag_name}, generated {len(rules)} rules", "transformed_code": code}
                    else:
                        return {"error": f"Flag '{flag_name}' not found in flags.json. Available flags: {list(FLAGS_CACHE['flags'].keys())}", "transformed_code": code}
                else:
                    return {"error": "flags.json not found in current directory", "transformed_code": code}
            except Exception as e:
                return {"error": f"Failed to load flags: {str(e)}", "transformed_code": code}
        elif rules is None:
            rules = []
            edges = edges or []
        # Convert dicts to Piranha objects
        rule_objs = []
        for r in rules:
            # Ensure required fields are present
            rule_dict = {
                "name": r.get("name", "unnamed_rule"),
                "query": r.get("query", ""),
                "is_seed_rule": r.get("is_seed_rule", False)
            }

            # Handle both replace and replace_node
            if "replace_node" in r:
                rule_dict["replace_node"] = r["replace_node"]
                rule_dict["replace"] = r.get("replace", "")
            else:
                rule_dict["replace"] = r.get("replace", "")

            rule_objs.append(Rule(**rule_dict))

        edge_objs = []
        for r in edges:
            edge_dict = {
                "from_rule": r.get("from_rule", ""),
                "to": r.get("to", ""),
                "scope": r.get("scope", "parent")
            }
            edge_objs.append(OutgoingEdges(**edge_dict))

        args = PiranhaArguments(
            code_snippet=code,
            language=language,
            rule_graph=RuleGraph(rules=rule_objs, edges=edge_objs),
        )

        summaries = execute_piranha(args)
        if summaries and len(summaries) > 0:
            return {"transformed_code": summaries[0].content}
        else:
            return {"transformed_code": code, "message": "No transformations applied", "debug": f"Generated {len(rules)} rules"}

    except Exception as e:
        error_msg = str(e)
        if "Cannot parse the tree-sitter query" in error_msg:
            return {
                "error": f"Invalid tree-sitter query syntax: {error_msg}. Please check the Piranha documentation for correct query syntax.",
                "transformed_code": code,
                "suggestion": "Try using simpler queries like 'if_stmt' or check the Piranha examples for proper syntax."
            }
        else:
            return {"error": f"Piranha execution failed: {error_msg}", "transformed_code": code}

# -------------------------------------------------------------------
# Tool: List Flags (reads from flags.json)
# -------------------------------------------------------------------
@app.tool
def list_flags(working_directory: str = None) -> dict:
    """
    List feature flags from flags.json file in the working directory.

    Reads a flags.json file from the specified working directory (or current directory)
    and parses flag definitions. The flags.json file should contain flag definitions
    in the format:

    {
      "functions": ["function1", "function2"],
      "flags": {
        "flag_name": {
          "value": true,
          "description": "What this flag controls",
          "replace_with": true
        }
      }
    }

    Args:
        working_directory: Directory to look for flags.json file (optional)

    Returns:
        A dictionary containing parsed flags and their information.
    """
    global FLAGS_CACHE

    if working_directory is None:
        working_directory = os.getcwd()

    flags_file = Path(working_directory) / "flags.json"

    if not flags_file.exists():
        return {
            "error": f"flags.json not found in {working_directory}",
            "flags": [],
            "suggestion": "Create a flags.json file with flag definitions"
        }

    try:
        with open(flags_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse the flags.json content
        parsed_data = parse_flags_json(content)
        flags = parsed_data["flags"]
        global_patterns = parsed_data["global_patterns"]

        # Store in global cache
        FLAGS_CACHE = {
            "flags": flags,
            "global_patterns": global_patterns
        }

        return {
            "flags": list(flags.keys()),
            "flag_details": flags,
            "global_patterns": global_patterns,
            "source_file": str(flags_file),
            "message": f"Loaded {len(flags)} flags and {len(global_patterns)} global patterns from {flags_file}"
        }

    except Exception as e:
        return {
            "error": f"Failed to read flags.json: {str(e)}",
            "flags": [],
            "source_file": str(flags_file)
        }

def parse_flags_json(content: str) -> dict:
    """
    Parse flags.json content to extract flag definitions and global function patterns.

    Expected format:
    {
      "functions": ["function1", "function2", "function3"],
      "flags": {
        "flag_name": {
          "value": true,
          "description": "Flag description",
          "replace_with": true
        }
      }
    }
    """
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {str(e)}")

    flags = {}
    global_patterns = data.get("functions", [])

    # Parse flags
    for flag_name, flag_data in data.get("flags", {}).items():
        value = flag_data.get("value")
        description = flag_data.get("description", "")
        replace_with = flag_data.get("replace_with", value)

        flags[flag_name] = {
            "value": str(value).lower() if isinstance(value, bool) else str(value),
            "description": description,
            "replace_with": str(replace_with).lower() if isinstance(replace_with, bool) else str(replace_with),
            "enabled": bool(value) if isinstance(value, bool) else str(value).lower() == 'true'
        }

    return {
        "flags": flags,
        "global_patterns": global_patterns
    }

def generate_rules_for_flag(flag_name: str, flag_info: dict, language: str) -> list[dict]:
    """
    Generate Piranha rules for a specific flag based on its information.

    Args:
        flag_name: Name of the flag
        flag_info: Flag information from flags.json
        language: Target programming language

    Returns:
        List of rule dictionaries for Piranha
    """
    global FLAGS_CACHE
    rules = []

    # Determine the replacement value based on flag state
    if flag_info["enabled"]:
        replace_value = flag_info.get("replace_with", "true")
    else:
        replace_value = "false"

    # Use global patterns - no fallback
    if not FLAGS_CACHE.get("global_patterns") or len(FLAGS_CACHE["global_patterns"]) == 0:
        return []

    # Create flexible patterns that match any function call with the flag name as a string parameter
    patterns = []
    for function_name in FLAGS_CACHE["global_patterns"]:
        # Create patterns that match the function with any parameters containing the flag name
        patterns.extend([
            f'{function_name}("{flag_name}")',  # Single parameter
            f'{function_name}("{flag_name}", $args)',  # Multiple parameters
            f'{function_name}($args, "{flag_name}")',  # Flag as second parameter
            f'{function_name}($args, "{flag_name}", $more_args)',  # Flag in middle
        ])

    # Create rules for each pattern
    for i, pattern in enumerate(patterns):
        rule = {
            "name": f"replace_{flag_name}_{i}",
            "query": f"cs {pattern}",
            "replace_node": "*",
            "replace": replace_value,
            "is_seed_rule": True
        }
        rules.append(rule)

    return rules

# -------------------------------------------------------------------
# Run the MCP server
# -------------------------------------------------------------------
if __name__ == "__main__":
    app.run()
