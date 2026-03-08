# 🎹 General MIDIfyer

**General MIDIfyer** is a powerful MIDI re-mapping and standardization tool designed to transform non-standard MIDI files into clean, compliant **General MIDI (GM)** files. Whether you are dealing with messy game rips, custom arrangements, or proprietary formats, this tool gives you surgical control over every instrument and drum kit.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-brightgreen.svg)

---

## ✨ Key Features

### 🛠 Precise Instrument Control
* **Solo & Mute:** Isolate or silence specific instruments in real-time to identify tracks effortlessly.
* **Transposition Suite:** Shift any instrument by **octaves** or **semitones** to fit the GM range or correct pitch offsets.
* **Volume Multiplier:** Fine-tune the mix with a percentage-based volume gain (%) for each individual instrument.

### 🔊 Advanced Playback & Tuning
* **SF2 Engine:** Play back the original MIDI using your preferred SoundFont (.SF2) via a built-in Fluidsynth integration.
* **Sample Preview:** Built-in pitch selector to play individual samples/instruments from the loaded SF2, helping you identify what is what before mapping.
* **"T" (Tone) Mode:** A dedicated tuning mode that plays a **Square Wave** at the instrument's pitch. This is a game-changer for precise tuning and alignment.

### 🥁 The Drum Specialist (Smart Mapping)
* **Simple Drum Mapping:** Quickly redirect any program change to a standard GM drum note.
* **Advanced Multi-Drum Mode:** Specifically designed for complex percussion tracks (like Tom-Toms, Bongos, or varied kits). It automatically **detects every unique note** used in a specific program change.
* **Smart Visual Alerts:** If you set a track to "Normal Drum" mode but the app detects **multiple pitches**, the track bar will **turn red**. This warns you that you should use "Multi-Drum" mode to avoid losing sonic variety.

### 🚀 Workflow & Export
* **Instant Preview:** Generate a temporary MIDI file with all your changes and open it automatically in your system's default MIDI player with a single click.
* **Config Persistence:** Don't lose your progress. Save your entire configuration into a `.json` file in the same folder as your MIDI. The app will automatically reload these settings the next time you open that file.
* **Clean Export:** Export your final, standardized General MIDI file ready for use in any DAW or hardware synth.

---

## 🛠 Installation & Requirements

To run **General MIDIfyer**, you will need:

1.  **Python 3.8+**
2.  **Fluidsynth** (for real-time audio playback)
3.  **Required Libraries:**
    ```bash
    pip install mido fluidsynth tkinterdnd2
    ```

---

## 🚀 How to use

1.  **Drag & Drop:** Toss your `.mid` and `.sf2` files into the interface.
2.  **Identify:** Use Solo/Mute and the Sample Preview to see what each track does.
3.  **Remap:** Change "Inst" to "Drum" or "Multi" as needed. 
    * *Watch out for the **Red Bar**! If it appears, that track has multiple percussion sounds that need Multi-Drum mapping.*
4.  **Tune:** Use the "T" mode and Transposition to align everything to GM standards.
5.  **Preview & Export:** Check your work with the Instant Preview and hit Export when it's perfect.

---

## 🤝 Contributing

Got ideas to make the MIDIfyer even better? Feel free to fork the repo, open issues, or submit pull requests!

---

*Developed with 🎶 by [Your Name/Username]*
