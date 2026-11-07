# Overtone Workouts

Workouts for Overtone, the iPhone app that plays a
spoken coach over your own music. The app lists the ones here in its library, and speaks the one you
choose into a workout on your phone.

Each workout is an Overtone script: plain text saying what the coach says and when, with tones,
rests, repeats and holds. See the [script format](SCRIPT-FORMAT.md) for how to write one.

## How it's laid out

| Folder | What's in it |
|---|---|
| `workouts/` | One script per workout, which can `@include` exercises and shared files |
| `exercises/<group>/` | One script per exercise, a single chapter, grouped by what it works (`legs`, `core`, `upper-body`, `full-body`, `cardio`) |
| `shared/` | What exercises and workouts include, such as the tones in `sounds.overtone` |
| `images/` | Artwork that workouts name |
| `drafts/` | Workouts being written: checked like the rest, but not published |
| `tools/workouts.py` | Puts a workout together as one file, checks everything, and writes the catalog |

## Adding a workout

Workouts from anyone are welcome. Send a pull request that adds one file to `workouts/`:

1. Name it `<activity>-<name>.overtone` in lower case, such as `running-hill-repeats.overtone`.
2. Give it a `@description` saying what it is and what's needed, and a `@workout` saying what it
   records in Health.
3. Build it from exercises where you can: `@include ../exercises/legs/squats.overtone` puts that
   exercise in as it is, and lines straight after it carry on its chapter. Write any chapter of your
   own in the workout itself. The 7-minute workout is an example.
4. Check it with `python3 tools/workouts.py check`, then try it in Overtone: put it together as one
   file with `python3 tools/workouts.py expand workouts/<name>.overtone > <name>.overtone`, and open
   that on your iPhone.

## Adding an exercise

Exercises are what workouts include, and what the app's New Workout builds workouts from. Each is
one file in the folder of what it works, such as `exercises/legs/squats.overtone`:

```
@include ../../shared/sounds.overtone

## Squats
Squats. Feet shoulder-width apart, sit back, chest up.
+0:00.5 [countdown]
--- 0:30
0:00 [go]
0:15 Halfway. Down until the thighs are level.
-0:05 Five seconds.
---
[stop]
```

It's one chapter, whose title is the exercise's name. Its first line says the name and then how to
do it, which New Workout uses as its tip. Its timed part (`--- 0:30`, 5 seconds to 10 minutes in
steps of 5) is how long it usually lasts; for as many as you can, use `@ladder` and no timed part,
so the app waits until the listener taps Next. `@track Reps` asks for a number as it finishes.

Only send what you wrote yourself, or have permission to share under this repository's licence.
Workouts are reviewed before they're merged, and the app shows them to everyone, so keep them
suitable for all ages.

## How it's published

On every pull request, a GitHub Action (`.github/workflows/publish.yml`) checks every workout,
draft and exercise with `tools/workouts.py`. On main, it also puts each workout together as one file
in `published/`, as the app adds it, writes `catalog.json` (each workout's title, length and
exercises, and the exercise list), and publishes the repository with them on GitHub Pages, where
the app reads them. Nothing generated is kept in the repository.

## Licence

The workouts, exercises and artwork are licensed under
[Creative Commons Attribution 4.0](LICENSE) (CC BY 4.0): anyone may use, share and adapt them,
giving credit.
