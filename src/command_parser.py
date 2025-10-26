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

# --- Intent Patterns ---
matcher = Matcher(nlp.vocab)

# Pattern for opening applications
open_app_patterns = [
    [{"LOWER": {"IN": ["open", "launch", "start"]}}, {"IS_ALPHA": True, "OP": "+"}],
    [{"LOWER": {"IN": ["open", "launch", "start"]}}, {"IS_ALPHA": True, "OP": "+"}, {"IS_ALPHA": True, "OP": "*"}]
]
matcher.add("open_app", open_app_patterns)

# Pattern for closing applications
close_app_patterns = [
    [{"LOWER": {"IN": ["close", "exit", "terminate", "quit"]}}, {"IS_ALPHA": True, "OP": "+"}],
    [{"LOWER": {"IN": ["close", "exit", "terminate", "quit"]}}, {"IS_ALPHA": True, "OP": "+"}, {"IS_ALPHA": True, "OP": "*"}]
]
matcher.add("close_app", close_app_patterns)

# Pattern for searching the web
search_patterns = [
    [{"LOWER": {"IN": ["search", "find", "look", "google"]}}, {"LOWER": "for", "OP": "?"}, {"IS_ALPHA": True, "OP": "+"}]
]
matcher.add("search", search_patterns)

# Pattern for getting the time
get_time_patterns = [
    [{"LOWER": "what"}, {"LOWER": "time"}, {"LOWER": "is"}, {"LOWER": "it"}],
    [{"LOWER": "get"}, {"LOWER": "the"}, {"LOWER": "time"}]
]
matcher.add("get_time", get_time_patterns)

# Pattern for answering questions
answer_question_patterns = [
    [{"LOWER": {"IN": ["what", "who"]}}, {"LOWER": {"IN": ["is", "are"]}}, {"IS_ALPHA": True, "OP": "+"}]
]
matcher.add("answer_question", answer_question_patterns)

# Patterns for system monitoring
get_cpu_patterns = [
    [{"LOWER": {"IN": ["what", "check"]}}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "cpu"}, {"LOWER": "usage"}]
]
matcher.add("get_cpu_usage", get_cpu_patterns)

# Patterns for alarms and reminders
set_reminder_patterns = [
    [{"LOWER": {"IN": ["set", "create", "add"]}}, {"LOWER": "a", "OP": "?"}, {"LOWER": "reminder"}, {"LOWER": "to"}, {"IS_ALPHA": True, "OP": "+"}]
]
matcher.add("set_reminder", set_reminder_patterns)

# Pattern for playing on YouTube
play_youtube_patterns = [
    [{"LOWER": "play"}, {"IS_ALPHA": True, "OP": "+"}, {"LOWER": "on"}, {"LOWER": "youtube"}]
]
matcher.add("play_on_youtube", play_youtube_patterns)

set_alarm_patterns = [
    [{"LOWER": {"IN": ["set", "create", "add"]}}, {"LOWER": "an", "OP": "?"}, {"LOWER": "alarm"}, {"LOWER": "for"}, {"IS_ALPHA": True, "OP": "+"}]
]
matcher.add("set_alarm", set_alarm_patterns)

# Patterns for file management
find_files_patterns = [
    [{"LOWER": "find"}, {"LOWER": "my", "OP": "?"}, {"IS_ALPHA": True, "OP": "+"}, {"LOWER": "files"}]
]
matcher.add("find_files", find_files_patterns)

move_files_patterns = [
    [{"LOWER": "move"}, {"LOWER": "all", "OP": "?"}, {"IS_ALPHA": True, "OP": "+"}, {"LOWER": "from"}, {"IS_ALPHA": True, "OP": "+"}, {"LOWER": "to"}, {"IS_ALPHA": True, "OP": "+"}]
]
matcher.add("move_files", move_files_patterns)

# Pattern for learning a face
learn_face_patterns = [
    [{"LOWER": "learn"}, {"LOWER": "my"}, {"LOWER": "face"}, {"LOWER": "as"}, {"IS_ALPHA": True, "OP": "+"}]
]
matcher.add("learn_face", learn_face_patterns)

# Pattern for reading text via OCR
read_text_patterns = [
    [{"LOWER": {"IN": ["read", "scan"]}}, {"LOWER": "this"}, {"LOWER": {"IN": ["document", "page", "text"]}}]
]
matcher.add("read_text", read_text_patterns)

# Pattern for identifying objects
identify_objects_patterns = [
    [{"LOWER": {"IN": ["what", "identify"]}}, {"LOWER": "do"}, {"LOWER": "you"}, {"LOWER": "see"}],
    [{"LOWER": "identify"}, {"LOWER": "objects"}]
]
matcher.add("identify_objects", identify_objects_patterns)

# Pattern for creating documents
create_document_patterns = [
    [{"LOWER": "create"}, {"LOWER": "document"}, {"LOWER": "about"}, {"IS_ALPHA": True, "OP": "+"}]
]
matcher.add("create_document", create_document_patterns)

get_memory_patterns = [
    [{"LOWER": {"IN": ["what", "check"]}}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "memory"}, {"LOWER": "usage"}]
]
matcher.add("get_memory_usage", get_memory_patterns)

get_battery_patterns = [
    [{"LOWER": {"IN": ["what", "check"]}}, {"LOWER": "is"}, {"LOWER": "the"}, {"LOWER": "battery"}, {"LOWER": "status"}]
]
matcher.add("get_battery_status", get_battery_patterns)

# Pattern for teaching a new command
teach_command_patterns = [
    [{"LOWER": "teach"}, {"LOWER": "command"}, {"IS_ALPHA": True, "OP": "+"}, {"LOWER": "to"}, {"IS_ALPHA": True, "OP": "+"}]
]
matcher.add("teach_command", teach_command_patterns)

# Pattern for explaining a document
explain_document_patterns = [
    [{"LOWER": {"IN": ["read", "explain", "summarize"]}}, {"LOWER": "and", "OP": "?"}, {"LOWER": "explain", "OP": "?"}, {"LOWER": "the", "OP": "?"}, {"LOWER": "file", "OP": "?"}, {"IS_ASCII": True, "OP": "+"}]
]
matcher.add("explain_document", explain_document_patterns)


def parse_command(text):
    """
    Parses a command from the user's speech using spaCy's Matcher.
    Returns the command and the extracted arguments.
    """
    if not text:
        return None, None

    doc = nlp(text)
    matches = matcher(doc)

    if not matches:
        return None, None

    # Get the best match (the one with the longest span)
    best_match = max(matches, key=lambda m: m[2] - m[1])
    match_id, start, end = best_match
    intent = nlp.vocab.strings[match_id]

    # Special handling for the 'teach_command' intent
    if intent == "teach_command":
        span = doc[start:end]
        # Extract command name and actions
        command_name_part = []
        actions_part = []
        parsing_actions = False
        for token in span:
            if token.lower_ == "to":
                parsing_actions = True
                continue
            if not parsing_actions and token.lower_ not in ["teach", "command"]:
                command_name_part.append(token.text)
            elif parsing_actions:
                actions_part.append(token.text)

        command_name = " ".join(command_name_part)
        actions = " ".join(actions_part).split(" and then ")
        return intent, (command_name, actions)

    # Extract the entity (the part of the text that isn't the keyword)
    span = doc[start:end]
    keywords_to_remove = {
        "open_app": ["open", "launch", "start"],
        "close_app": ["close", "exit", "terminate", "quit"],
        "search": ["search", "for", "find", "look", "google"],
        "answer_question": ["what", "who", "is", "are"],
        "set_reminder": ["set", "a", "reminder", "to"],
        "set_alarm": ["set", "an", "alarm", "for"],
        "play_on_youtube": ["play", "on", "youtube"],
        "find_files": ["find", "my", "files"],
        "move_files": ["move", "all", "from", "to"],
        "learn_face": ["learn", "my", "face", "as"],
        "explain_document": ["read", "explain", "summarize", "and", "the", "file"]
    }.get(intent, [])

    entity = " ".join([token.text for token in span if token.lower_ not in keywords_to_remove])

    return intent, entity.strip()
