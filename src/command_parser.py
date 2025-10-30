import spacy
from spacy.matcher import Matcher

# Load the spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# --- Intent Definition ---
# A mapping of intents to their patterns and argument extraction logic.
INTENT_PATTERNS = {
    "open_app": {
        "patterns": [
            [{"LOWER": {"IN": ["open", "launch", "start"]}}, {"IS_ALPHA": True, "OP": "+"}]
        ],
        "args": [{"name": "app_name", "type": "ENT_TYPE", "value": "APP_NAME"}]
    },
    "close_app": {
        "patterns": [
            [{"LOWER": {"IN": ["close", "exit", "terminate"]}}, {"IS_ALPHA": True, "OP": "+"}]
        ],
        "args": [{"name": "app_name", "type": "ENT_TYPE", "value": "APP_NAME"}]
    },
    "search": {
        "patterns": [
            [{"LOWER": {"IN": ["search", "find", "google"]}}, {"LOWER": "for", "OP": "?"}, {"TEXT": {"REGEX": ".*"}, "OP": "+"}]
        ],
        "args": [{"name": "query", "type": "REGEX", "value": "for (.*)"}]
    },
    "play_on_youtube": {
        "patterns": [
            [{"LOWER": "play"}, {"TEXT": {"REGEX": ".*"}}, {"LOWER": "on"}, {"LOWER": "youtube"}]
        ],
        "args": [{"name": "video_title", "type": "REGEX", "value": "play (.*) on youtube"}]
    },
    "get_time": {"patterns": [[{"LOWER": "what"}, {"LOWER": "time"}, {"LOWER": "is"}, {"LOWER": "it"}]]},
    "get_date": {"patterns": [[{"LOWER": "what"}, {"LOWER": "is"}, {"LOWER": "today's"}, {"LOWER": "date"}]]},
    "answer_question": {
        "patterns": [
            [{"LOWER": {"IN": ["what", "who"]}}, {"LOWER": {"IN": ["is", "are"]}}, {"TEXT": {"REGEX": ".*"}, "OP": "+"}]
        ],
        "args": [{"name": "query", "type": "REGEX", "value": "(is|are) (.*)"}]
    },
    "move_files": {
        "patterns": [
            [{"LOWER": "move"}, {"OP": "*"}, {"LOWER": "from"}, {"ENT_TYPE": "SRC_DIR", "OP": "+"}, {"LOWER": "to"}, {"ENT_TYPE": "DEST_DIR", "OP": "+"}]
        ],
        "args": [
            {"name": "file_type", "type": "REGEX", "value": "move (.*) from"},
            {"name": "source", "type": "ENT_TYPE", "value": "SRC_DIR"},
            {"name": "destination", "type": "ENT_TYPE", "value": "DEST_DIR"}
        ]
    },
     "teach_command": {
        "patterns": [
            [{"LOWER": "teach"}, {"LOWER": "command"}, {"TEXT": {"REGEX": ".*?"}}, {"LOWER": "to"}, {"TEXT": {"REGEX": ".*"}}]
        ],
        "args": [
            {"name": "command_name", "type": "REGEX", "value": "command (.*?) to"},
            {"name": "actions", "type": "REGEX", "value": "to (.*)"}
        ]
    },
    # Add other intents here...
}

# --- Entity Patterns for Ruler ---
# This helps spaCy recognize custom entities like APP_NAME, file paths, etc.
def setup_ruler(nlp_object):
    if "entity_ruler" not in nlp_object.pipe_names:
        ruler = nlp_object.add_pipe("entity_ruler", before="ner")
        patterns = [
            {"label": "APP_NAME", "pattern": [{"LOWER": {"IN": ["chrome", "vscode", "notepad", "calculator"]}}]},
            {"label": "SRC_DIR", "pattern": [{"LOWER": {"IN": ["downloads", "documents", "desktop"]}}]},
            {"label": "DEST_DIR", "pattern": [{"LOWER": {"IN": ["downloads", "documents", "desktop", "pictures"]}}]}
        ]
        ruler.add_patterns(patterns)

# --- Main Parser Logic ---
def initialize_parser():
    """Initializes the spaCy Matcher and Entity Ruler."""
    matcher = Matcher(nlp.vocab)
    for intent, data in INTENT_PATTERNS.items():
        matcher.add(intent, data["patterns"])
    setup_ruler(nlp)
    return matcher

matcher = initialize_parser()

def parse_command(text):
    """
    Parses a command using a combination of keyword matching and custom logic.
    Returns the intent and a dictionary of extracted arguments.
    """
    if not text:
        return None, {}

    # Simple keyword-based intent recognition for complex commands
    if "teach command" in text and "to" in text:
        intent = "teach_command"
    elif "play" in text and "on youtube" in text:
        intent = "play_on_youtube"
    elif "move" in text and "from" in text and "to" in text:
        intent = "move_files"
    else:
        # Fallback to spaCy Matcher for other commands
        doc = nlp(text)
        matches = matcher(doc)
        if not matches:
            return None, {}
        best_match = max(matches, key=lambda m: doc[m[1]:m[2]].end - doc[m[1]:m[2]].start)
        intent = nlp.vocab.strings[best_match[0]]

    args = {}
    if intent == 'teach_command':
        parts = text.split(' to ')
        command_part = parts[0].replace('teach command', '').strip()
        actions_part = parts[1]
        args['command_name'] = command_part
        args['actions'] = [a.strip() for a in actions_part.split(' and then ')]
    elif intent == 'play_on_youtube':
        args['video_title'] = text.replace('play', '').replace('on youtube', '').strip()
    elif intent == 'move_files':
        parts = text.split(' from ')
        file_type = parts[0].replace('move', '').strip()
        source_dest = parts[1].split(' to ')
        args['file_type'] = file_type
        args['source'] = source_dest[0].strip()
        args['destination'] = source_dest[1].strip()
    else: # Default argument extraction for Matcher-based intents
        span = doc[best_match[1]:best_match[2]]
        if intent == 'open_app':
            args['app_name'] = " ".join([token.text for token in span if token.lower_ not in ["open", "launch", "start"]])
        elif intent == 'close_app':
            args['app_name'] = " ".join([token.text for token in span if token.lower_ not in ["close", "exit", "terminate"]])
        elif intent == 'search':
            args['query'] = " ".join([token.text for token in span if token.lower_ not in ["search", "for", "find", "google"]])
        elif intent == 'answer_question':
            args['query'] = " ".join([token.text for token in span if token.lower_ not in ["what", "is", "who", "are"]])

    # Clean up any empty args that may result
    for key, value in list(args.items()):
        if not value:
            del args[key]

    return intent, args
