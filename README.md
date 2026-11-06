# Overtone Workouts

Workouts for Overtone, the iPhone app that plays a
spoken coach over your own music. The app lists the ones here in its examples, and speaks the one you
choose into a workout on your phone.

Each workout is an Overtone script: plain text saying what the coach says and when, with tones,
rests, repeats and holds. See the [script format](SCRIPT-FORMAT.md) for how to write one.

## Adding a workout

Workouts from anyone are welcome. Send a pull request that adds one file to `workouts/`:

1. Write the script, and try it in Overtone first: open the file on your iPhone, or make it in the
   app's script editor and share it from there.
2. Name it `<activity>-<name>.overtone` in lower case, such as `running-hill-repeats.overtone`.
3. Put everything in that one file: no `@include`, and any artwork as a `data:` URI (the app does
   this when it shares a script).
4. Give it a `@description` saying what it is and what's needed, and a `@workout` saying what it
   records in Health.

## Adding an exercise

Exercises are what the app's New Workout builds workouts from. Each is one small file in
`exercises/`, named `<group>-<name>.json`, such as `legs-squats.json`:

```json
{
  "name": "Squats",
  "tip": "Feet shoulder-width apart, sit back, chest up.",
  "seconds": 30,
  "group": "Legs"
}
```

| Field | What it is |
|---|---|
| `name` | Said as it starts, and shown in the list. Needed |
| `group` | What it works, such as `Legs`, `Core`, `Upper Body`, `Full Body` or `Cardio`. Needed |
| `tip` | Said after its name: how to do it |
| `seconds` | How long it usually lasts, 5 to 600 in steps of 5; 30 if not given |
| `holds` | `true` for as many as you can: the app waits until the listener taps Next |
| `tracked` | A number to ask for as it finishes, such as `Reps` |
| `equipment` | What it needs, such as `Chair`; leave it out for nothing |

Don't edit `catalog.json` or `artwork/`: they're written from the scripts and exercises when a pull request is merged.

Only send what you wrote yourself, or have permission to share under this repository's licence.
Workouts are reviewed before they're merged, and the app shows them to everyone, so keep them
suitable for all ages.

## Licence

The workouts, exercises and artwork are licensed under
[Creative Commons Attribution 4.0](LICENSE) (CC BY 4.0): anyone may use, share and adapt them,
giving credit.
