# Overtone scripts

<!-- A copy of the script format from the Overtone app's documentation. -->

An Overtone script is a guide track written as plain text: what's said and
played, and when. Overtone opens one itself: it speaks each line at its
time and adds the result as an episode, with its chapters, repeats, rest,
tracking and workout (see [Opening a script in Overtone](#opening-a-script-in-overtone)).
A script can reuse what it defines, pick lines at random and fill a
stretch of time, and random lines are picked each time the episode is
made, so making it again gives new picks.

```
# Hill Session
@description Hills, with a warm-up and a cool-down.
@speech rate 1.1
@workout running

@define [go]:
  @tone{pitch 988 Hz, length 0:00.15, volume 0.5}
  +0:00.05 @tone{pitch 1318 Hz, length 0:00.45, volume 0.5}

## Warm-up
Easy jog to the bottom of the hill.

## Hill
@repeat 6
@track Seconds
Hill repeat. Up on the tone.
--- 1:15
0:00 [go]
0:30 Halfway. Drive the arms.
-0:15 Fifteen seconds. Push.
```

A script is UTF-8 text, usually named `<name>.overtone.txt`. Overtone shares
scripts as `<name>.overtone`, a type it opens when one is tapped in Files
or another app; it reads either, and any other `.txt` file.

## Lines

Every line is one of these:

| Line | What it is |
|---|---|
| `# Title`, `## Chapter` | The script's title; a chapter |
| `@name{options} argument` | An instruction |
| `[name]` | Plays what's defined as `name` |
| `---` | Starts a part |
| `// note` | A note for whoever edits the file. It isn't said |
| Anything else | Said |

A line that's said or played can start with a time; the rest of the line
is what plays then.

### Instructions

An instruction starts with `@`. Its options go in braces straight after its
name, separated by commas, and the rest of the line is its argument:

```
@say{pan -0.85} Front left.
@random{fill, no repeats} [front], [back]
@track{step 5} kg
```

A line that's only text is `@say` without options, and a line that's only
`[name]` is `@play` without options. To say something that starts with
`@`, `[`, `{` or `\`, start the line with `\`, which isn't said.

An instruction that ends with a comma carries on on the next line.

| Instruction | What it plays | Options |
|---|---|---|
| `@say text` | The text | `pan` |
| `@play [name]` | What's defined as `name` | `pan`, `fill` |
| `@tone` | A tone | `pitch 880 Hz` and `length 0:00.12`, both needed; `volume`, `pan` |
| `@random [a], [b]` | One of them; see [Random](#random) | `pan`, `fill`, `no repeats`, `at most N in a row`, `seed N` |

`pan` is where it's heard, from `-1` (left) through `0` to `1` (right). The
side it's panned to plays it at full level, and the other side at
`1 - |pan|` of that, so a line panned part of the way is still heard in a
single earbud; around `±0.85` is clearly to one side. On a definition or a
random line, it's for the lines in it that don't have their own. A
script with any panned line is made in stereo.

A tone's `volume` is relative to the voice: `1` peaks about as loud as a
typical line, and `0.5` half as loud. It's from `0.1` to `2`, and `1` if
not given.

### Times

A time is minutes and seconds, `m:ss`, with an optional fraction: `1:30`,
`0:02.4`; or hours, minutes and seconds, `1:02:03`.

| Line | When it's said or played |
|---|---|
| `Text to say.` | Half a second after the line before finishes |
| `+0:00.7 Text to say.` | 0.7 s after the line before finishes |
| `0:15 Text to say.` | 15 s into the part |
| `-0:03 Text to say.` | 3 s before the next line with a time like `0:15`, or before the part ends if there's none |
| `+0:02`, `0:15`, `-0:03` | Nothing, at that time: the next line follows on from then |

So `+0:02` alone is a pause, and `0:15` alone holds what follows until
0:15, or ends a fill there. A countdown stays with what it counts down to, and `-0:10 Ten seconds.`
at the end of a part stays ten seconds before its end. Lines with times
like `0:15` come in order, within their part.

Text without a time that runs over several lines is one line: lines next
to each other are joined with spaces. Leave a blank line between two that
should be said separately.

## Chapters and parts

Each `## title` starts a chapter: what Overtone lists, jumps between, and
can repeat or track. Its settings go straight under the title:

| Setting | What it does |
|---|---|
| `@repeat 3` | The chapter plays three times, 1 to 10 |
| `@track Reps` | Overtone asks for a number at the end of the chapter, and the episode's statistics chart it: `@track{step 5} kg`, where the step is how much one click of the watch's crown changes it, 1, 2, 5 or 10 |
| `@ladder` | A level of a ladder: playback holds once it's played, until the listener plays it again or moves on |
| `@rest` | A rest chapter, to explain what's next: it shows as a rest, isn't numbered, and counts towards the rest after it; see [Rests](#rests) |
| `@artwork data:image/jpeg;base64,...` | Shown while the chapter plays, instead of the script's artwork; see [Images](#images) |

A chapter is made of parts, each with its own clock. `--- 3:00` starts a
part that lasts three minutes, whatever is said in it; a bare `---` one
that lasts as long as its lines. Times like `0:15` count from the start of
their part. A drill is usually three parts: the announcement, the timed
drill, and the tone that ends it, so the drill lasts exactly as long
however long the announcement takes.

A repeated chapter plays all its parts again each time, with the same
words; random lines are picked again. For anything played only once (an
announcement before the first round, or "last one" on the final pass),
use separate chapters.

## Definitions

`@define [name]:` names what its indented lines play, so it can be played
anywhere with `[name]`. Its lines are written as a chapter's are, with
their own clock: a time like `0:02` counts from where the definition
starts playing, and it can have parts. Its first line starts as it does.
A definition with one line can have it after the colon.

```
@define [front left]:
  @say{pan -0.85} Front left
  +0:01.7 [beep]
  +0:02

@define [front]: @random [front left], [front right]
```

`[front left]` says the call, plays the beep 1.7 s after it, then waits 2 s,
so whatever comes next starts then.

A definition of only tones and pauses, none of them panned, is a sound:

```
@define [countdown]:
  @tone{pitch 880 Hz, length 0:00.12, volume 0.5}
  +0:00.88 @tone{pitch 880 Hz, length 0:00.12, volume 0.5}
  +0:00.88 @tone{pitch 880 Hz, length 0:00.12, volume 0.5}
  +0:00.88
```

Definitions go anywhere outside a chapter. When a name is defined twice,
the last definition is used.

## Random

`@random [a], [b], [c]` plays one of them, picked at random. A name listed
twice is picked twice as often. A definition that's only a random pick,
like `[front]` above, is a group, and picks go on through it: `@random
[front], [back]` plays front left, front right, back left or back right.

| Option | What it does |
|---|---|
| `fill` | Plays again and again, each as the one before ends, until the next line if it has a time like `0:50`, or the end of the part if it's the last line and the part has a length, while the next one fits. With neither, it plays once |
| `no repeats` | Never the same twice running, after any groups |
| `at most 2 in a row` | The same at most twice running: with two to choose from, `no repeats` would only alternate |
| `seed 52` | Picks the same every time |

`fill` works on `@play` too: `0:01 @play{fill} [tick]` ticks until the next
line. A fill knows what fits from how long each line takes once spoken.
When nothing fits, Overtone says so as it makes the episode.

## Settings

At the top of the script, under the title:

| Setting | What it is |
|---|---|
| `@description` | What the script is; shown before it is added |
| `@author` | Shown under the title |
| `@speech rate 1.1` | How fast to speak: `0.5` to `2`, `1` is the voice's normal pace. Approximate. Overtone uses the speed chosen with the voice instead |
| `@minimum gap 0:00.8` | The least time between a line with a time like `0:15` and a line before it that runs long. Default 0.3 s |
| `@workout running` | The workout the Apple Watch records while it plays; see [Workouts](#workouts) |
| `@rest 1:00` | Rest between chapters; see [Rests](#rests) |
| `@artwork data:image/jpeg;base64,...` | The episode's artwork; see [Images](#images) |

A setting's value can carry on over the next lines if they start with two
spaces. The voice isn't a setting: it's chosen, with the speed, as the
script is added.

## Including other files

`@include ../shared/sounds.overtone` puts that file's lines in at that
point, as they are, with its path relative to the file with the
`@include`; `@artwork` can name an image file the same way. A workout
here can include exercises from `exercises/`, and an exercise includes
the sounds it plays. The app puts a workout together as one file as
it adds it, leaving out definitions nothing plays and the copies of
sounds every exercise includes; `python3 tools/workouts.py expand` does
the same, to try one before sending it.

## How the audio is laid out

Nothing in the script says how long a line takes to say: that depends on
the voice. Each line is measured once it's spoken (a sound's length is
known from its tones), then they're laid out like this:

1. Chapters follow one another, each starting where the one before ends.
   Within a chapter, parts follow one another the same way, and so do
   the parts of a definition.
2. A line without a time, or with a `+` time, starts that long after the
   line before it ends.
3. A line with a time like `0:15` starts at that time, unless the line
   before it is still playing then. In that case it starts
   `@minimum gap` after that line ends, and every line after it may move
   later too.
4. A part with a length lasts exactly that long, unless a line runs past
   its end: then it is lengthened to end 0.5 s after that line, with a
   warning.
5. A part without a length ends when its last line finishes.

So a time like `0:15` is the earliest a line can start. A line that moves
isn't an error, but Overtone lists every one that moved
by more than half a second, and every lengthened part, so a script can be
corrected where the timing matters.

## Rests

The rest plays between chapters and between repeats of a chapter, never
before the first chapter or after the last. A rest is
5 seconds to a minute in steps of 5 seconds, or up to 3 minutes in steps
of 15, and a `@rest` between these is rounded to the nearest, with a
warning. The rest is silence (the music
comes back up), with any beeps the listener has chosen in Settings: at
its start, and at its end. The rest is made long enough for both. Overtone's
beeps play only in rests, never over a chapter.

A chapter with `@rest` under its title is a rest chapter: it's said
like any other, and shows as a rest, so it can talk through the
exercise after it while the exercise itself keeps to its tones and a cue
or two. Before a rest chapter, only the start beeps play, in a rest just
long enough for them. After one, the rest plays for whatever's left of
it once those and the rest chapter have played (none when the rest
chapter is longer), followed by the end beeps, as after any rest. Rest
chapters before the first exercise, such as an introduction, are
followed only by the end beeps, and those after the last exercise, such
as a cool-down, by nothing: neither is made up to a whole rest. So a
rest chapter shouldn't start or end on beeps of its own, or leave room
for them: Overtone adds them. The end beeps also play when the listener
moves on early, with Next or after a hold on the rest chapter.

```
## Squats, explained
@rest
Next, squats. Feet shoulder-width apart, chest up.

## Squats
--- 0:30
0:00 [go]
-0:05 Five seconds.
``` The
listener can change the rest, the repeats and which chapters play after
adding the script, without changing it.

## Workouts

`strength`, `functionalStrength`, `hiit`, `core`, `crossTraining`,
`mixedCardio`, `jumpRope`, `running`, `walking`, `hiking`, `cycling`,
`rowing`, `elliptical`, `stairClimbing`, `swimming`, `squash`, `tennis`,
`badminton`, `tableTennis`, `racquetball`, `pickleball`, `soccer`,
`basketball`, `volleyball`, `americanFootball`, `rugby`, `hockey`,
`baseball`, `cricket`, `handball`, `boxing`, `kickboxing`, `martialArts`,
`fencing`, `wrestling`, `yoga`, `pilates`, `barre`, `taiChi`,
`flexibility`, `mindAndBody`, `cooldown`, `dance`, `climbing`, `golf`,
`other`.

An unknown name is ignored with a warning, so the episode records no
workout.

## Images

An image is a data URI: `data:image/jpeg;base64,<data>`, or `image/png`
for a PNG, with standard base64 and no line breaks. Square images look
best: Overtone shows artwork square, and keeps the episode's at most 1400
pixels on its longest side and a chapter's at most 1200.

## Mistakes

A script with a mistake isn't added, and Overtone says where it is:

```
Line 42: nothing is defined as [sides].
Line 57: this is past the part's end.
shared/warm-up.txt, line 12: this comes before the line with a time above it.
```

## Writing a good script

- **Write for the ear.** "Three sets of ten", not "3×10"; "two minutes",
  not "2'". Spell out abbreviations and units.
- **Time each line by what it depends on.** Lines that follow on from
  each other have no time or a `+` time, so rewording one moves the rest
  along with it. Only lines tied to a moment have a time like `0:15`, and
  countdowns count back, `-0:10`, so they stay right if the part's length
  changes.
- **Give speech of unknown length its own part.** An announcement before
  a timed interval goes in a part without a length, then the interval in
  a part with one.
- **Leave room before fixed lines.** Speech runs at roughly 2.5 words a
  second at the normal rate, so a ten-word line takes about 4 s.
- **Short lines, spoken at the moment they matter.** "Go" at 0:00 and
  "Ten seconds" at 1:20 work better than one long line at the start.
- **Keep the end of a timed part clear.** A line still playing when the
  part is due to end lengthens it, so a timed interval runs long.
- **Use chapters for what the listener might repeat, skip or track:**
  each set or interval is a chapter.

## Opening a script in Overtone

Overtone can also write a script: **+** → **New Script…** in a
playlist, or **Replace** → **Edit Script…** on an episode made from one. It shows
the chapters, parts and lines described here, and **Text** shows the
script itself; what it makes is the same text.

Add a script with the **+** button in a playlist (**Add Files…**), as
you would an audio file, or open it in Overtone from Files or another
app's share sheet, which adds it to Up Next. Overtone speaks it with the
voice chosen as it's added and adds the episode when it's done: a minute
or two for a typical session. Meanwhile it's a row at the end of the
playlist showing its progress, and the rest of the app can be used as
normal. Keep Overtone open until it's done; if it closes first, the
script carries on the next time Overtone opens. Each line spoken is kept,
so adding the script again after an edit only speaks the lines that
changed.

The voices are Apple's, installed on the iPhone, or Kokoro's: natural
neural voices in American English that run on the iPhone. Kokoro's
voices are downloaded, and deleted, together in Settings → Voice: about
255 MB.
