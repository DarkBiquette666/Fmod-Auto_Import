# FMOD Importer Debug Context

## Project Overview
This is a standalone Python tool (Tkinter GUI) that generates FMOD Studio Project XML files directly to "import" audio assets.
It operates by:
1.  Reading the `.fspro` and `Workspace.xml` to understand project structure.
2.  Creating or Modifying XML files in the `Metadata/Event` folder.
3.  Assigning these events to Banks (modifying `Metadata/Bank/{id}.xml`).

## The Problem
**Symptom:** When opening the project in FMOD Studio 2.03 after import, the newly created events are flagged with **"Invalid Component"** errors in the "Project Validation" dialog.
**Consequence:** Because the events are considered invalid/malformed, FMOD refuses to assign them to Banks properly (or the bank assignment in XML is ignored).

## Technical Details

### Implementation Method
The tool uses Python's `xml.etree.ElementTree` to construct the Event XML from scratch (for "Auto-Create") or via deep-copy (for "Template").
Code location: `fmod_importer/core/event_creator.py` (`create_from_scratch` method).

### Current XML Structure (Generated)
We are generating an `objects` root with `serializationModel="Studio.02.03.00"` (dynamically matched to project).

The `Event` object contains:
- `GroupTrack` (Dynamic)
- `Timeline` (Dynamic)
- `MixerInput` -> `MixerBusEffectChain` -> `MixerBusPanner`
- `MasterTrack` -> `EventMixerMaster` -> `MixerBusEffectChain` -> `MixerBusFader`
- `EventAutomatableProperties` (with `maxVoices=1`, `voiceStealing=3`)

### Applied Fixes (RESOLVED)

1.  **Serialization Version Mismatch**:
    *   *Issue:* Tool was hardcoding `Studio.02.02.00`. Project is `Studio.02.03.00`.
    *   *Fix:* Updated `EventCreator`, `BankManager`, and `BusManager` to use the version from `Workspace.xml`.

2.  **Invalid MixerInput Fader (REVERTED/INVALID)**:
    *   *Previous Theory:* We thought `MixerBusFader` in `MixerInput` was invalid.
    *   *Correction:* `valid_event.xml` (FMOD 2.03) **DOES** have a fader in `MixerInput`. The code correctly generates it. The previous diagnosis was incorrect.

3.  **Extraneous Property on EventMixerMaster (FIXED)**:
    *   *Issue:* The tool was adding `<property name="name"><value>Master</value></property>` to `EventMixerMaster`.
    *   *Finding:* `valid_event.xml` does **not** have a `name` property on the `EventMixerMaster` (it is implicitly "Master"). This extra property likely causes the "Invalid Component" error in FMOD 2.03.
    *   *Fix:* Removed the `name` property from `EventMixerMaster` in `create_from_scratch` and filtered it out in `copy_from_template`.

4.  **Bank Assignment Issue (LIKELY FIXED)**:
    *   *Symptom:* Only the "fixed" event was assigned to a bank; others were unassigned.
    *   *Cause:* FMOD likely discards relationships (like bank assignments) for events it deems "Invalid".
    *   *Resolution:* By fixing the XML structure (Fix #3) and ensuring correct versioning (Fix #1), all generated events should now be valid, allowing FMOD to correctly process their bank assignments.

## Next Steps
Test the import with all fixes applied. All events should now:
1.  Pass FMOD validation (no "Invalid Component").
2.  Be correctly assigned to their Banks.
