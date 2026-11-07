#!/usr/bin/env python3
"""Puts the workouts here together and checks them, and writes the catalog the app reads.

    python3 tools/workouts.py expand workouts/hiit-1-seven-minute.overtone > seven-minute.overtone
    python3 tools/workouts.py check
    python3 tools/workouts.py catalog

`expand` writes a script as one file, with what it includes put in, its artwork as a data URI, and
the definitions nothing plays left out: what Overtone opens. `check` reads every workout, draft and
exercise, and stops at the first mistake. `catalog` checks them too, then writes each workout put
together to published/, the artwork of those that have theirs as a data URI to artwork/, and
catalog.json, which GitHub Pages serves with the rest, and the app reads.

The format is SCRIPT-FORMAT.md. This reads enough of it to check what the catalog relies on and
what's easy to get wrong; Overtone reads every script fully before playing it.
"""
import base64
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CATALOG_VERSION = 1
WORDS_PER_SECOND = 2.5
MINIMUM_GAP = 0.3
FILE_SETTINGS = ["description", "author", "speech rate", "minimum gap", "workout", "rest", "artwork"]
CHAPTER_SETTINGS = ["ladder", "rest", "repeat", "track", "artwork"]
INSTRUCTIONS = sorted(["say", "play", "tone", "random", "define", "include", *FILE_SETTINGS, *CHAPTER_SETTINGS],
                      key=len, reverse=True)
NAME = re.compile(r"\[([^\[\]]+)\]")


class ScriptError(Exception):
    pass


# MARK: - Expanding


def resolve(relative, path):
    """`relative`, named in the file at `path` (None for the script), as a path relative to the script."""
    parts = [p for p in (path.rsplit("/", 1)[0].split("/") if path and "/" in path else [])]
    for part in relative.split("/"):
        if part == ".":
            continue
        if part == "..":
            if not parts or parts[-1] == "..":
                parts.append("..")
            else:
                parts.pop()
        else:
            parts.append(part)
    return "/".join(parts)


def argument(instruction, line):
    if not line.startswith(instruction + " "):
        return None
    return line[len(instruction) + 1:].strip() or None


class Expansion:
    def __init__(self):
        self.lines = []
        self.includes = []  # (marker line, range of the included file's lines)

    def append(self, inner, path):
        marker = len(self.lines)
        self.lines.append(f"// From {path}:")
        start = len(self.lines)
        self.lines += inner.lines
        self.includes += [(m + start, range(r.start + start, r.stop + start)) for m, r in inner.includes]
        self.includes.append((marker, range(start, len(self.lines))))


def expanded(text, path, including, read):
    expansion = Expansion()
    for index, line in enumerate(text.split("\n")):
        place = f"{path}, line {index + 1}" if path else f"Line {index + 1}"
        trimmed = line.strip()
        include = None if line.startswith(" ") else argument("@include", trimmed)
        artwork = None if line.startswith(" ") else argument("@artwork", trimmed)
        if include:
            included = resolve(include, path)
            if included in including or included == path:
                raise ScriptError(f"{place}: {include} includes itself.")
            try:
                inner_text = read(included).decode("utf-8")
            except (OSError, UnicodeDecodeError):
                raise ScriptError(f"{place}: couldn't read {include}.")
            if inner_text.endswith("\n"):
                inner_text = inner_text[:-1]
            inner = expanded(inner_text, included, including + ([path] if path else []), read)
            expansion.append(inner, included)
        elif artwork and not artwork.startswith("data:"):
            try:
                data = read(resolve(artwork, path))
            except OSError:
                data = b""
            if not data:
                raise ScriptError(f"{place}: couldn't read the artwork {artwork}.")
            kind = "png" if data.startswith(b"\x89PNG") else "jpeg"
            expansion.lines.append(f"@artwork data:image/{kind};base64,{base64.b64encode(data).decode()}")
        else:
            expansion.lines.append(line)
    return expansion


def is_comment(line):
    return line.strip().startswith("//")


def is_blank(line):
    return not line.strip()


def uses(line):
    return set(NAME.findall(line))


def definitions(lines, markers):
    """Every @define: its lines (with any comment just above it), its text, and what it plays."""
    found = []
    index = 0
    while index < len(lines):
        match = None if lines[index].startswith(" ") else re.match(
            r"^@define(?:\{[^}]*\})? +\[([^\[\]]+)\]:(.*)$", lines[index])
        if not match:
            index += 1
            continue
        start = index
        while start > 0 and start - 1 not in markers and not lines[start - 1].startswith(" ") \
                and is_comment(lines[start - 1]):
            start -= 1
        end = index + 1
        played = uses(match.group(2))
        while end < len(lines):
            if lines[end].startswith("  ") and not is_comment(lines[end]):
                played |= uses(lines[end])
                end += 1
                continue
            if end in markers or not (lines[end].startswith("  ") or is_comment(lines[end]) or is_blank(lines[end])):
                break
            following = next((i for i in range(end, len(lines))
                              if not is_comment(lines[i]) and not is_blank(lines[i])), None)
            if following is None or not lines[following].startswith("  ") \
                    or any(m in markers for m in range(end, following)):
                break
            end = following
        text = "\n".join(l.strip() for l in lines[index:end] if l.strip() and not is_comment(l))
        found.append({"name": match.group(1), "lines": range(start, end), "text": text, "uses": played})
        index = end
    return found


def remove_unused_definitions(expansion):
    """Leaves out definitions nothing plays, and copies of one defined again: the one played is the
    last, kept where its first identical copy is. Then included files left with only comments."""
    lines = expansion.lines
    markers = {m for m, _ in expansion.includes}
    found = definitions(lines, markers)
    defined = {i for d in found for i in d["lines"]}
    kept = {}
    for definition in reversed(found):
        if definition["name"] not in kept:
            kept[definition["name"]] = next(d for d in found
                                            if d["name"] == definition["name"] and d["text"] == definition["text"])
    unvisited = set()
    for i, line in enumerate(lines):
        if i not in defined and i not in markers and not is_comment(line):
            unvisited |= uses(line)
    used = set()
    while unvisited:
        name = unvisited.pop()
        if name in used:
            continue
        used.add(name)
        if name in kept:
            unvisited |= kept[name]["uses"] - used
    removed = set()
    for definition in found:
        if definition["name"] not in used or kept[definition["name"]]["lines"] != definition["lines"]:
            removed |= set(definition["lines"])
    for marker, included in sorted(expansion.includes, key=lambda include: -include[0]):
        if all(i in removed or is_blank(lines[i]) or is_comment(lines[i]) for i in included):
            removed.add(marker)
            removed |= set(included)
    output = []
    for i, line in enumerate(lines):
        if i in removed:
            continue
        if is_blank(line) and (not output or is_blank(output[-1])):
            continue
        output.append(line)
    while output and is_blank(output[-1]):
        output.pop()
    expansion.lines = output
    expansion.includes = []


def expand(path, remove_unused=True):
    """The script at `path` as one file."""
    def read(relative):
        return (path.parent / relative).read_bytes()
    text = path.read_text(encoding="utf-8")
    expansion = expanded(text[:-1] if text.endswith("\n") else text, None, [], read)
    if remove_unused:
        remove_unused_definitions(expansion)
    return "\n".join(expansion.lines) + "\n"


# MARK: - Reading


def seconds(text, place):
    """"1:30", "1:02:03", "0:45.5", with an optional + or -, as seconds."""
    unsigned = text[1:] if text[:1] in "+-" else text
    match = re.fullmatch(r"(?:(\d+):)?(\d+):(\d\d(?:\.\d+)?)", unsigned)
    if not match or float(match.group(3)) >= 60:
        raise ScriptError(f'{place}: "{text}" isn\'t a time; times are m:ss, as in 1:30 or 0:02.4')
    return int(match.group(1) or 0) * 3600 + int(match.group(2)) * 60 + float(match.group(3))


def instruction(text, place):
    """`@name{options} argument` as (name, options, argument), or None if `text` isn't one."""
    if not text.startswith("@"):
        return None
    rest = text[1:]
    name = next((n for n in INSTRUCTIONS if rest.startswith(n) and not rest[len(n):len(n) + 1].isalpha()), None)
    if name is None:
        word = re.match(r"[A-Za-z]*", rest).group(0)
        raise ScriptError(f"{place}: @{word} isn't an instruction")
    match = re.fullmatch(r"(?:\{([^}]*)\})?(?: (.*))?", rest[len(name):])
    if not match:
        raise ScriptError(f"{place}: this should be @{name}{{options}} argument")
    return name, match.group(1) or "", (match.group(2) or "").strip()


def options(text, place):
    result = {}
    for option in (o.strip() for o in text.split(",")):
        if not option:
            continue
        key, _, value = option.partition(" ")
        if key == "in":
            key, value = "in a row", option[len("in a row"):].strip()
        elif option.startswith("at most"):
            key = "in a row"
        result[key] = value.strip()
    if "length" in result:
        result["length"] = seconds(result["length"], place)
    return result


class Body:
    """A chapter's or definition's parts, each a duration and lines."""

    def __init__(self):
        self.parts = [{"duration": None, "lines": []}]
        self.saying = False

    def read(self, line, place, after_blank):
        part = re.fullmatch(r"---(?: (.+))?", line)
        if part:
            self.parts.append({"duration": seconds(part.group(1), place) if part.group(1) else None, "lines": []})
            self.saying = False
            return
        timing, content = ("next", None), line
        timed = re.fullmatch(r"([+-]?\d+:\d\d(?::\d\d)?(?:\.\d+)?)(?: (.+))?", line)
        if timed:
            time = seconds(timed.group(1), place)
            kind = {"+": "after", "-": "before"}.get(timed.group(1)[0], "at")
            timing, content = (kind, time), timed.group(2)
        lines = self.parts[-1]["lines"]
        if content is None:
            lines.append({"timing": timing, "kind": ("say", ""), "fills": False})
            self.saying = False
            return
        plain = not content.startswith(("@", "[", "{", "\\"))
        if not timed and plain and self.saying and not after_blank and lines and lines[-1]["kind"][0] == "say":
            lines[-1]["kind"] = ("say", lines[-1]["kind"][1] + " " + content)
            return
        new = self.line(content, timing, place)
        lines.append(new)
        self.saying = new["kind"][0] == "say"

    @staticmethod
    def line(content, timing, place):
        def line(kind, fills=False):
            return {"timing": timing, "kind": kind, "fills": fills}
        if content.startswith("\\"):
            return line(("say", content[1:]))
        name = NAME.fullmatch(content)
        if name:
            return line(("play", name.group(1)))
        if content.startswith(("[", "{")):
            raise ScriptError(f"{place}: a sound is [name] on its own; start the line with \\ to say it")
        parsed = instruction(content, place)
        if parsed is None:
            return line(("say", content))
        command, option_text, arg = parsed
        if command not in ("say", "play", "tone", "random"):
            raise ScriptError(f"{place}: @{command} can't go here; a chapter's lines are text, [name], "
                              "@say, @play, @tone and @random")
        opts = options(option_text, place)
        if command == "say":
            return line(("say", arg))
        if command == "tone":
            if "length" not in opts or "pitch" not in opts:
                raise ScriptError(f"{place}: a tone is @tone{{pitch 880 Hz, length 0:00.12}}")
            return line(("tone", opts["length"]))
        names = [NAME.fullmatch(n.strip()) for n in arg.split(",")]
        if not names or not all(names):
            raise ScriptError(f"{place}: @{command} takes [names], as in @{command} [beep]")
        if command == "play":
            return line(("play", names[0].group(1)), "fill" in opts)
        return line(("random", [n.group(1) for n in names]), "fill" in opts)


def joined(text):
    """`text`'s lines as (number, line), an instruction ending in a comma joined with the next line."""
    result, carrying = [], False
    for index, line in enumerate(text.split("\n")):
        line = line.rstrip()
        trimmed = line.strip()
        if carrying and trimmed and not trimmed.startswith("//"):
            result[-1] = (result[-1][0], result[-1][1] + " " + trimmed)
        else:
            result.append((index + 1, line))
        if not trimmed:
            carrying = False
        elif not trimmed.startswith("//"):
            last = result[-1][1].strip()
            carrying = last.endswith(",") and re.match(r"^(?:[+-]?\d+:\d\d(?::\d\d)?(?:\.\d+)? )?@", last) is not None
    return result


def read_script(text, name):
    """The script `text` (put together already) as its title, settings, definitions and chapters."""
    script = {"title": None, "settings": {}, "definitions": {}, "chapters": []}
    chapter = block = setting = None
    blank = False
    for number, line in joined(text):
        place = f"{name}, line {number}"
        trimmed = line.strip()
        if trimmed.startswith("//"):
            continue
        if not trimmed:
            blank = True
            continue
        after_blank, blank = blank, False
        if line.startswith("  "):
            if block is not None:
                block.read(trimmed, place, after_blank)
                continue
            if setting and not after_blank:
                script["settings"][setting] += " " + trimmed
                continue
        block = setting = None
        parsed = instruction(trimmed, place)
        if trimmed.startswith("# "):
            if script["title"] is not None or script["chapters"]:
                raise ScriptError(f"{place}: the title goes once, at the top of the script")
            script["title"] = trimmed[2:].strip()
        elif trimmed.startswith("## "):
            chapter = {"title": trimmed[3:].strip(), "settings": {}, "body": Body()}
            script["chapters"].append(chapter)
        elif parsed and parsed[0] == "include":
            raise ScriptError(f"{place}: @include is put in by expand first")
        elif parsed and parsed[0] == "define":
            match = re.fullmatch(r"\[([^\[\]]+)\]:(?: (.+))?", parsed[2])
            if not match:
                raise ScriptError(f"{place}: a definition is @define [name]:, with its lines indented under it")
            block = Body()
            if match.group(2):
                block.read(match.group(2), place, False)
            script["definitions"][match.group(1)] = block
        elif chapter is not None:
            if parsed and parsed[0] in CHAPTER_SETTINGS:
                if chapter["body"].parts[0]["lines"] or len(chapter["body"].parts) > 1:
                    raise ScriptError(f"{place}: a chapter's settings go straight under its title")
                chapter["settings"][parsed[0]] = parsed[2]
            else:
                chapter["body"].read(trimmed, place, after_blank)
        else:
            if not parsed or parsed[0] not in FILE_SETTINGS:
                raise ScriptError(f"{place}: before the first chapter go only settings "
                                  f"({', '.join('@' + s for s in FILE_SETTINGS)}), @define and @include")
            script["settings"][parsed[0]] = parsed[2]
            setting = parsed[0]
    if not script["title"]:
        raise ScriptError(f"{name}: a script starts with its title, as in # Hill Repeats")
    if not script["chapters"]:
        raise ScriptError(f"{name}: a script needs at least one ## chapter")
    check_names(script, name)
    return script


def check_names(script, name):
    """Every name played is defined."""
    bodies = [(f"chapter “{c['title']}”", c["body"]) for c in script["chapters"]]
    bodies += [(f"[{n}]", b) for n, b in script["definitions"].items()]
    for where, body in bodies:
        for part in body.parts:
            for line in part["lines"]:
                kind, value = line["kind"]
                played = [value] if kind == "play" else value if kind == "random" else []
                for played_name in played:
                    if played_name not in script["definitions"]:
                        raise ScriptError(f"{name}: {where} plays [{played_name}], which isn't defined")


# MARK: - Estimating


def estimated_duration(script):
    """About how long the episode lasts, before it's spoken: as Overtone estimates it, each line taking
    as long as its words would and each sound its tones. The rests between chapters aren't counted, as
    the app adds them as it plays."""
    # Overtone speaks at the speed chosen with the voice, so the script's own rate is left out.
    rate = 1
    gap = seconds(script["settings"]["minimum gap"], "minimum gap") if "minimum gap" in script["settings"] \
        else MINIMUM_GAP
    lengths, measuring = {}, set()

    def length_of_name(name):
        if name in lengths:
            return lengths[name]
        if name not in script["definitions"] or name in measuring:
            return 0
        measuring.add(name)
        length = lay_out(script["definitions"][name].parts, True)
        measuring.discard(name)
        lengths[name] = length
        return length

    def length_of(kind):
        what, value = kind
        if what == "say":
            return len(value.split()) / (WORDS_PER_SECOND * rate)
        if what == "play":
            return length_of_name(value)
        if what == "tone":
            return value
        return sum(length_of_name(n) for n in value) / len(value) if value else 0

    def fixed_time(index, part):
        kind, value = part["lines"][index]["timing"]
        if kind == "at":
            return value
        if kind == "before":
            for later in part["lines"][index + 1:]:
                if later["timing"][0] == "at":
                    return max(later["timing"][1] - value, 0)
            return max(part["duration"] - value, 0) if part["duration"] is not None else None
        return None

    def lay_out_part(part, starts_definition):
        fixed = [fixed_time(i, part) for i in range(len(part["lines"]))]
        previous_end = None
        for index, line in enumerate(part["lines"]):
            if fixed[index] is not None:
                start = fixed[index]
                if previous_end is not None and previous_end > start:
                    start = previous_end + gap
            else:
                kind, value = line["timing"]
                after = value if kind == "after" else (0 if starts_definition and index == 0 else 0.5) \
                    if kind == "next" else 0
                start = (previous_end or 0) + after
            end = start + length_of(line["kind"])
            until = fixed[index + 1] if index + 1 < len(part["lines"]) else part["duration"]
            if line["fills"] and until is not None:
                end = max(until, start)
            previous_end = end
        length = previous_end or 0
        if part["duration"] is not None:
            length = length + 0.5 if length > part["duration"] else part["duration"]
        return length

    def lay_out(parts, is_definition):
        return sum(lay_out_part(p, is_definition and i == 0) for i, p in enumerate(parts))

    return sum(max(lay_out(chapter["body"].parts, False), 0.1) * max(int(chapter["settings"].get("repeat") or 1), 1)
               for chapter in script["chapters"])


# MARK: - The catalog


def first_line(chapter):
    lines = chapter["body"].parts[0]["lines"]
    return lines[0]["kind"][1] if lines and lines[0]["kind"][0] == "say" else None


def tip(line, name):
    """`line` without `name` at its start: "Squats. Chest up." is "Chest up."."""
    if line is None:
        return None
    if line.lower().startswith(name.lower()):
        line = line[len(name):].lstrip(".:,;! ")
    return line or None


def group_title(folder):
    """"upper-body" is "Upper Body"."""
    return " ".join(word[:1].upper() + word[1:] for word in folder.split("-"))


def workout_entry(path, script, artwork):
    settings = script["settings"]
    entry = {
        "id": path.stem,
        "title": script["title"],
        "author": settings.get("author"),
        "description": settings.get("description"),
        "activity": settings.get("workout"),
        "exercises": sum(1 for c in script["chapters"] if "rest" not in c["settings"]),
        "seconds": round(estimated_duration(script)),
        "file": f"published/{path.name}",
        "artwork": artwork,
    }
    return {k: v for k, v in entry.items() if v is not None}


def exercise_entry(path, script, name):
    if len(script["chapters"]) != 1:
        raise ScriptError(f"{name}: it should be one chapter, not {len(script['chapters'])}")
    chapter = script["chapters"][0]
    if "rest" in chapter["settings"]:
        raise ScriptError(f"{name}: it's a rest chapter")
    holds = "ladder" in chapter["settings"]
    length = next((p["duration"] for p in chapter["body"].parts if p["duration"] is not None), None)
    if length is None and not holds:
        raise ScriptError(f"{name}: it needs a timed part, such as --- 0:30, or @ladder")
    if not holds and not (5 <= length <= 600 and length % 5 == 0):
        raise ScriptError(f"{name}: its timed part should last 5 to 600 seconds, in steps of 5")
    entry = {
        "id": f"{path.parent.name}/{path.stem}",
        "name": chapter["title"],
        "tip": tip(first_line(chapter), chapter["title"]),
        "seconds": None if holds else int(length),
        "holds": True if holds else None,
        "tracked": chapter["settings"].get("track") or None,
        "group": group_title(path.parent.name),
    }
    return {k: v for k, v in entry.items() if v is not None}


def scripts(directory):
    return sorted((ROOT / directory).glob("*.overtone"), key=lambda p: p.name)


def published(path):
    """`path` put together as one file, as the app adds it. The app speaks at the speed chosen with
    the voice, so a script's own rate, which renderers use, is left out."""
    return "".join(line for line in expand(path).splitlines(keepends=True) if not line.startswith("@speech rate "))


def read(path, title=None):
    name = path.relative_to(ROOT).as_posix()
    text = expand(path)
    if title:
        text = f"# {title}\n" + text
    return text, read_script(text, name)


def workout_artwork(path, script, artwork_dir):
    """Where a workout's artwork is, relative to the catalog: the image it names, or one written from
    its data URI."""
    source = re.search(r"^@artwork (\S+)", path.read_text(encoding="utf-8"), re.M)
    if not source:
        return None
    if not source.group(1).startswith("data:"):
        return (path.parent / source.group(1)).resolve().relative_to(ROOT).as_posix()
    match = re.fullmatch(r"data:image/(png|jpeg);base64,(.+)", script["settings"]["artwork"])
    if not match:
        raise ScriptError(f"{path.relative_to(ROOT)}: its artwork should be a PNG or JPEG")
    if artwork_dir:
        file = artwork_dir / f"{path.stem}.{'png' if match.group(1) == 'png' else 'jpg'}"
        file.write_bytes(base64.b64decode(match.group(2)))
        return file.relative_to(ROOT).as_posix()
    return None


def catalog(write):
    artwork_dir, published_dir = ROOT / "artwork", ROOT / "published"
    if write:
        for directory in (artwork_dir, published_dir):
            directory.mkdir(exist_ok=True)
            for old in directory.iterdir():
                old.unlink()
    workouts = []
    for path in scripts("workouts"):
        _, script = read(path)
        if write:
            (published_dir / path.name).write_text(published(path), encoding="utf-8")
        workouts.append(workout_entry(path, script, workout_artwork(path, script, artwork_dir if write else None)))
        minutes = round(workouts[-1]["seconds"] / 60)
        print(f"{path.name}: {script['title']}, about {minutes} min, {workouts[-1]['exercises']} exercises")
    if not workouts:
        raise ScriptError("No workouts/*.overtone.")
    for path in scripts("drafts"):
        read(path)
        print(f"drafts/{path.name}: checked, not published")
    exercises = []
    for group in sorted(p for p in (ROOT / "exercises").iterdir() if p.is_dir()):
        for path in scripts(f"exercises/{group.name}"):
            name = path.relative_to(ROOT).as_posix()
            _, script = read(path, title=path.stem)
            exercises.append(exercise_entry(path, script, name))
    if write:
        document = {"version": CATALOG_VERSION, "workouts": workouts, "exercises": exercises}
        (ROOT / "catalog.json").write_text(json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
                                           encoding="utf-8")
        print(f"Wrote catalog.json with {len(workouts)} workouts and {len(exercises)} exercises.")
    else:
        print(f"Checked {len(workouts)} workouts and {len(exercises)} exercises.")


def main(arguments):
    try:
        if len(arguments) == 2 and arguments[0] == "expand":
            path = Path(arguments[1]).resolve()
            text = expand(path)
            read_script(text, arguments[1])
            sys.stdout.write(text)
        elif arguments == ["check"]:
            catalog(write=False)
        elif arguments == ["catalog"]:
            catalog(write=True)
        else:
            sys.exit(__doc__.strip().split("\n\n")[1])
    except ScriptError as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main(sys.argv[1:])
