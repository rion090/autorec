{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://github.com/rion090/autorec/profiles/schemas/ctf.schema.json",
  "title": "AutoRec CTF Profile",
  "description": "Schema for validating ctf.json recon profiles",
  "type": "object",
  "required": ["profile", "description", "aggressive_mode", "docker_support", "phases"],
  "additionalProperties": false,
  "properties": {
    "profile": {
      "type": "string",
      "description": "Unique profile identifier (e.g. ctf_player)"
    },
    "description": {
      "type": "string",
      "description": "Human-readable description of what this profile does"
    },
    "aggressive_mode": {
      "type": "boolean",
      "description": "When true, tools may run with noisier / faster flags"
    },
    "docker_support": {
      "type": "boolean",
      "description": "Reserved for future Docker-based tool execution"
    },
    "phases": {
      "type": "object",
      "description": "Named phases (e.g. default, probing). At least one required.",
      "minProperties": 1,
      "additionalProperties": {
        "$ref": "#/$defs/phase"
      }
    }
  },
  "$defs": {
    "phase": {
      "type": "object",
      "required": ["description", "requires_manual_approval", "tools"],
      "additionalProperties": false,
      "properties": {
        "description": {
          "type": "string"
        },
        "requires_manual_approval": {
          "type": "boolean",
          "description": "If true, the user must confirm before this phase runs"
        },
        "aggressive_mode": {
          "type": "boolean"
        },
        "tools": {
          "type": "array",
          "minItems": 1,
          "items": {
            "$ref": "#/$defs/tool"
          }
        }
      }
    },
    "tool": {
      "type": "object",
      "required": ["name", "verify_cmd"],
      "additionalProperties": false,
      "properties": {
        "name": {
          "type": "string",
          "description": "CLI binary name (e.g. nmap, httpx)"
        },
        "flags": {
          "type": "string",
          "description": "Extra flags passed to the tool (space-separated)"
        },
        "verify_cmd": {
          "type": "string",
          "description": "Command used to confirm the tool is installed (e.g. nmap --version)"
        },
        "install": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "apt": { "type": "string" },
            "go":  { "type": "string" },
            "pip": { "type": "string" },
            "git": { "type": "string" }
          }
        }
      }
    }
  }
}
