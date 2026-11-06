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

Don't edit `catalog.json` or `artwork/`: they're written from the scripts when a workout is merged.

Only send what you wrote yourself, or have permission to share under this repository's licence.
Workouts are reviewed before they're merged, and the app shows them to everyone, so keep them
suitable for all ages.

## Licence

The workouts and their artwork are licensed under
[Creative Commons Attribution 4.0](LICENSE) (CC BY 4.0): anyone may use, share and adapt them,
giving credit.
