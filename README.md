# Flag Sweeper

A Model Context Protocol (MCP) server that uses Polyglot Piranha to automatically clean up feature flags in your codebase. Transform feature flag calls into their final values based on flag states defined in `flags.md`.

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install fastmcp polyglot-piranha
   ```

2. **Configure in Cursor:**
   Add to `~/.cursor/mcp.json`:
   ```json
   {
     "mcpServers": {
       "mcp-piranha": {
         "command": "python3",
         "args": ["-m", "mcp-piranha"],
         "cwd": "/path/to/your/project",
         "env": {
           "PYTHONPATH": "/path/to/your/project"
         }
       }
     }
   }
   ```

3. **Create `flags.md` in your project:**
   ```markdown
   # Feature Flags

   ## Functions
   isFeatureEnabled,client.GetString,isEnabled,getFlag,is_feature_enabled

   ## Flags
   beta_ui:true:Enables the new beta user interface:true
   new_checkout:false:New payment processing flow:false
   ```

## 🛠️ MCP Tools

### `list_flags`
Loads and parses feature flags from `flags.md` in your project directory.

**Parameters:**
- `working_directory` (optional): Directory to search for `flags.md`

**Returns:**
- `flags`: List of flag names
- `flag_details`: Detailed flag information
- `global_patterns`: Function patterns for detection
- `source_file`: Path to the loaded `flags.md`

### `apply_rewrite`
Transforms code by replacing feature flag calls with their final values.

**Parameters:**
- `code`: Source code to transform
- `language`: Programming language (go, java, python, etc.)
- `flag_name` (optional): Specific flag to clean up
- `rules` (optional): Custom Piranha rules
- `edges` (optional): Custom rule edges

**Returns:**
- `transformed_code`: The transformed code
- `message`: Status message

## 📝 `flags.md` Format

Ultra-concise format for defining feature flags and detection patterns:

```markdown
# Feature Flags

## Functions
function1,function2,function3

## Flags
flag_name:value:description:replace_with
```

### Format Details

**Functions Section:**
- Comma-separated list of function names to detect
- Examples: `isFeatureEnabled`, `client.GetString`, `isEnabled`
- Supports any function that takes the flag name as a string parameter

**Flags Section:**
- Format: `name:value:description:replace_with`
- `name`: Flag identifier
- `value`: Current state (true/false)
- `description`: Human-readable description
- `replace_with`: What to replace with when cleaning up
- Minimal format: `name:value` (description and replace_with default to value)

### Example

```markdown
# Feature Flags

## Functions
isFeatureEnabled,client.GetString,isEnabled,getFlag,is_feature_enabled,get_flag,flag_manager.is_feature_enabled,config.getBoolean,settings.isEnabled

## Flags
beta_ui:true:Enables the new beta user interface with modern design elements:true
new_checkout_flow:false:New payment processing flow with improved UX:false
feature_flag:true:Generic feature flag for testing purposes:true
legacy_auth:false:Legacy authentication system (deprecated):false
debug_mode:true:Enables debug logging and additional error information:true
```

## 🔧 How It Works

1. **Pattern Detection**: Uses global function patterns to find feature flag calls
2. **Flexible Matching**: Supports various function signatures:
   - `isFeatureEnabled("flag_name")`
   - `isFeatureEnabled("flag_name", arg2)`
   - `isFeatureEnabled(arg1, "flag_name")`
   - `isFeatureEnabled(arg1, "flag_name", arg3)`
3. **Rule Generation**: Creates Piranha rules for each function pattern
4. **Code Transformation**: Replaces flag calls with their final values

## 🧪 Testing

Run tests in the `tests/` directory:

```bash
python3 tests/test_multilayered.py
```

## 📁 Project Structure

```
mcp-piranha/
├── src/
│   ├── __init__.py
│   └── server.py          # Main MCP server
├── tests/
│   ├── test_multilayered.py
│   └── test_*.py          # Additional test files
├── __main__.py            # Entry point
├── flags.md               # Feature flag definitions
└── README.md
```

## 🎯 Supported Languages

- Go
- Java
- Python
- JavaScript/TypeScript
- C#
- And more via Polyglot Piranha

## 🔍 Example Transformations

**Before:**
```go
if isFeatureEnabled("beta_ui") {
    renderBetaUI()
} else {
    renderStandardUI()
}
```

**After (beta_ui: true):**
```go
if true {
    renderBetaUI()
} else {
    renderStandardUI()
}
```

**After (beta_ui: false):**
```go
if false {
    renderBetaUI()
} else {
    renderStandardUI()
}
```

## 🚨 Troubleshooting

- **"No transformations applied"**: Check that `flags.md` exists and contains the flag
- **"Connection closed"**: Restart Cursor or the MCP server
- **"Invalid tree-sitter query"**: Ensure function patterns are valid identifiers
