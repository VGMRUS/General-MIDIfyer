import os
import sys
import time
import json
import mido
import tempfile
import platform
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD


def get_resource_path(filename):
    """ Busca el archivo en la carpeta del script o dentro del bundle de PyInstaller """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

# Try to import fluidsynth
try:
    import fluidsynth
    HAS_FLUIDSYNTH = True
except ImportError:
    HAS_FLUIDSYNTH = False

# --- MIDI CONSTANTS ---
GM_INST_NAMES = [
    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano", "Honky-tonk Piano",
    "Electric Piano 1", "Electric Piano 2", "Harpsichord", "Clavi", "Celesta", "Glockenspiel",
    "Music Box", "Vibraphone", "Marimba", "Xylophone", "Tubular Bells", "Dulcimer",
    "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ", "Reed Organ", "Accordion",
    "Harmonica", "Tango Accordion", "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)",
    "Electric Guitar (jazz)", "Electric Guitar (clean)", "Electric Guitar (muted)",
    "Overdriven Guitar", "Distortion Guitar", "Guitar harmonics", "Acoustic Bass",
    "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass", "Slap Bass 1",
    "Slap Bass 2", "Synth Bass 1", "Synth Bass 2", "Violin", "Viola", "Cello", "Contrabass",
    "Tremolo Strings", "Pizzicato Strings", "Orchestral Harp", "Timpani", "String Ensemble 1",
    "String Ensemble 2", "SynthStrings 1", "SynthStrings 2", "Choir Aahs", "Voice Oohs",
    "Synth Voice", "Orchestra Hit", "Trumpet", "Trombone", "Tuba", "Muted Trumpet", "French Horn",
    "Brass Section", "SynthBrass 1", "SynthBrass 2", "Soprano Sax", "Alto Sax", "Tenor Sax",
    "Baritone Sax", "Oboe", "English Horn", "Bassoon", "Clarinet", "Piccolo", "Flute",
    "Recorder", "Pan Flute", "Blown Bottle", "Shakuhachi", "Whistle", "Ocarina",
    "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)", "Lead 4 (chiff)",
    "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass + lead)",
    "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)", "Pad 5 (bowed)",
    "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)", "FX 1 (rain)", "FX 2 (soundtrack)",
    "FX 3 (crystal)", "FX 4 (atmosphere)", "FX 5 (brightness)", "FX 6 (goblins)",
    "FX 7 (echoes)", "FX 8 (sci-fi)", "Sitar", "Banjo", "Shamisen", "Koto", "Kalimba",
    "Bag pipe", "Fiddle", "Shanai", "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock",
    "Taiko Drum", "Melodic Tom", "Synth Drum", "Reverse Cymbal", "Guitar Fret Noise",
    "Breath Noise", "Seashore", "Bird Tweet", "Telephone Ring", "Helicopter", "Applause", "Gunshot"
]

GM_DRUM_NAMES = {
    35: "Acoustic Bass Drum", 36: "Bass Drum 1", 37: "Side Stick", 38: "Acoustic Snare",
    39: "Hand Clap", 40: "Electric Snare", 41: "Low Floor Tom", 42: "Closed Hi Hat",
    43: "High Floor Tom", 44: "Pedal Hi-Hat", 45: "Low Tom", 46: "Open Hi Hat",
    47: "Low-Mid Tom", 48: "Hi-Mid Tom", 49: "Crash Cymbal 1", 50: "High Tom",
    51: "Ride Cymbal 1", 52: "Chinese Cymbal", 53: "Ride Bell", 54: "Tambourine",
    55: "Splash Cymbal", 56: "Cowbell", 57: "Crash Cymbal 2", 58: "Vibraslap",
    59: "Ride Cymbal 2", 60: "Hi Bongo", 61: "Low Bongo", 62: "Mute Hi Conga",
    63: "Open Hi Conga", 64: "Low Conga", 65: "High Timbale", 66: "Low Timbale",
    67: "High Agogo", 68: "Low Agogo", 69: "Cabasa", 70: "Maracas", 71: "Short Whistle",
    72: "Long Whistle", 73: "Short Guiro", 74: "Long Guiro", 75: "Claves",
    76: "Hi Wood Block", 77: "Low Wood Block", 78: "Mute Cuica", 79: "Open Cuica",
    80: "Mute Triangle", 81: "Open Triangle"
}

GM_INST_LIST = [f"{i}: {name}" for i, name in enumerate(GM_INST_NAMES)]
GM_DRUMS_LIST = [f"{k}: {v}" for k, v in sorted(GM_DRUM_NAMES.items())]

def clamp(v, mn=0, mx=127): return max(mn, min(mx, int(v)))

class AdvancedMidiEditor(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("General MIDIfyer 1.0")
        self.geometry("1300x750")
        self.config(bg="#1a1a1a")

        self.midi = None
        self.midi_path = None
        self.config_path = None
        self.program_notes = {} 
        
        self.sf2_path = None
        self.synth = None
        self.sfid = None
        self.sfid_tune = None

        self.rows = {} 
        self.live_mapping = {}
        self.any_solo = False
        self.is_playing = False
        self.play_thread = None

        self._build_ui()
        self._setup_dnd()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        header = tk.Frame(self, bg="#2c3e50", pady=10)
        header.pack(fill="x")
        self.lbl_info = tk.Label(header, text="Drag and drop a .MID and .SF2 to start", fg="white", bg="#2c3e50", font=("Arial", 12, "bold"))
        self.lbl_info.pack()
        self.lbl_sf2 = tk.Label(header, text="SF2: None", fg="#f1c40f", bg="#2c3e50", font=("Arial", 10))
        self.lbl_sf2.pack()

        mf = tk.Frame(self, bg="#1a1a1a")
        mf.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(mf, bg="#1a1a1a", highlightthickness=0)
        scroll = ttk.Scrollbar(mf, orient="vertical", command=self.canvas.yview)
        self.sf = tk.Frame(self.canvas, bg="#1a1a1a")
        self.sf.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.sf, anchor="nw")
        self.canvas.configure(yscrollcommand=scroll.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        btn_f = tk.Frame(self, bg="#111", pady=15)
        btn_f.pack(fill="x", side="bottom")
        self.btn_play = tk.Button(btn_f, text="▶ PLAY ORIGINAL", bg="#9b59b6", fg="white", width=22, font=("Arial", 9, "bold"), command=self.toggle_playback)
        self.btn_play.pack(side="left", padx=(15, 5))
        tk.Label(btn_f, text="Start at (s):", fg="white", bg="#111").pack(side="left", padx=(5, 2))
        self.start_time_var = tk.IntVar(value=0)
        tk.Spinbox(btn_f, from_=0, to=9999, increment=2, textvariable=self.start_time_var, width=4, bg="#333", fg="white").pack(side="left", padx=(0, 15))
        tk.Button(btn_f, text="PREVIEW MIDI (TEMP)", bg="#3498db", fg="white", width=20, command=self.preview_midi).pack(side="left", padx=15)
        tk.Button(btn_f, text="EXPORT MIDI", bg="#2ecc71", fg="white", width=15, command=self.export_midi).pack(side="right", padx=15)
        tk.Button(btn_f, text="SAVE CONFIG", bg="#f39c12", fg="white", width=20, command=self.save_config).pack(side="right", padx=15)

    def _setup_dnd(self):
        self.drop_target_register(DND_FILES)
        self.dnd_bind('<<Drop>>', self.handle_drop)

    def handle_drop(self, event):
        filepath = event.data.strip("{} ")
        ext = filepath.lower().split('.')[-1]
        if ext in ['mid', 'midi']: self.load_midi(filepath)
        elif ext in ['sf2', 'sf3']: self.load_sf2(filepath)

    def load_sf2(self, path):
        if not HAS_FLUIDSYNTH: 
            messagebox.showerror("Error", "Fluidsynth not available.")
            return
        self.sf2_path = path
        self.lbl_sf2.config(text=f"SF2: {os.path.basename(path)}")
        if self.synth: self.synth.delete()
        self.synth = fluidsynth.Synth()
        self.synth.start(driver="dsound" if os.name == "nt" else "alsa")
        self.sfid = self.synth.sfload(self.sf2_path)
        
        tune_path = get_resource_path("tuning.sf2")
        if os.path.exists(tune_path):
            self.sfid_tune = self.synth.sfload(tune_path)
            self.synth.program_select(15, self.sfid_tune, 0, 0)
        else: self.sfid_tune = None

    def load_midi(self, filepath):
        try:
            self.midi = mido.MidiFile(filepath)
            self.midi_path = filepath
            self.config_path = os.path.splitext(filepath)[0] + "_settings.json"
            self.lbl_info.config(text=f"MIDI: {os.path.basename(filepath)}")
        except: return

        for widget in self.sf.winfo_children(): widget.destroy()
        self.rows.clear()
        self.program_notes.clear()
        
        programs = set()
        active_program = {ch: 0 for ch in range(16)}
        for track in self.midi.tracks:
            for msg in track:
                if hasattr(msg, 'channel') and msg.type == 'program_change':
                    active_program[msg.channel] = msg.program
                    programs.add(msg.program)
                elif msg.type == 'note_on' and msg.velocity > 0:
                    prog = active_program.get(getattr(msg, 'channel', 0), 0)
                    if prog not in self.program_notes: self.program_notes[prog] = set()
                    self.program_notes[prog].add(msg.note)
                    
        if not programs: programs.add(0)
        for prog in sorted(programs): self.create_row(prog)
        self.load_config()

    def update_live_mapping(self):
        for prog, v in self.rows.items():
            prev_multi = self.live_mapping.get(prog, {}).get('multi_drums', {})
            self.live_mapping[prog] = {
                'type': v['type'].get().lower(),
                'target': v['target'].get(),
                'solo': v['solo'].get(),
                'mute': v['mute'].get(),
                'tuning': v['tuning'].get(),
                'transpose': (v['octave'].get() * 12) + v['semitone'].get(),
                'multi_drums': prev_multi
            }
        self.any_solo = any(m['solo'] for m in self.live_mapping.values())

    def create_row(self, prog):
        row_bg = "#222"
        f = tk.Frame(self.sf, bg=row_bg, pady=5)
        f.pack(fill="x", padx=10, pady=2)
        
        name = GM_INST_NAMES[prog] if prog < len(GM_INST_NAMES) else f"Prog {prog}"
        lbl_p = tk.Label(f, text=f"P{prog:03}", fg="#777", bg=row_bg, width=4)
        lbl_p.pack(side="left")
        lbl_name = tk.Label(f, text=name[:15], fg="#00ffcc", bg=row_bg, width=15, anchor="w", font=("Arial", 9, "bold"))
        lbl_name.pack(side="left")

        s_var, m_var, t_var_tune = tk.BooleanVar(value=False), tk.BooleanVar(value=False), tk.BooleanVar(value=False)
        t_var, target_var = tk.StringVar(value="Inst"), tk.StringVar()
        vol_var, key_var = tk.IntVar(value=100), tk.IntVar(value=60)
        oct_var, semi_var = tk.IntVar(value=0), tk.IntVar(value=0)

        def toggle_btn(v, b, active_color): 
            v.set(not v.get())
            b.config(bg=active_color if v.get() else "#444", fg="black" if v.get() and active_color != "#3498db" else "white")
            self.update_live_mapping()

        btn_s = tk.Button(f, text="S", width=2, bg="#444", fg="white", font=("Arial", 8, "bold"), command=lambda: toggle_btn(s_var, btn_s, "#E6DB74")); btn_s.pack(side="left", padx=1)
        btn_m = tk.Button(f, text="M", width=2, bg="#444", fg="white", font=("Arial", 8, "bold"), command=lambda: toggle_btn(m_var, btn_m, "#F92672")); btn_m.pack(side="left", padx=1)
        btn_t = tk.Button(f, text="T", width=2, bg="#444", fg="white", font=("Arial", 8, "bold"), command=lambda: toggle_btn(t_var_tune, btn_t, "#3498db")); btn_t.pack(side="left", padx=1)

        cb_t = ttk.Combobox(f, textvariable=t_var, values=["Inst", "Drum", "Multi"], width=6, state="readonly")
        cb_t.pack(side="left", padx=5)

        action_frame = tk.Frame(f, bg=row_bg)
        action_frame.pack(side="left", padx=5)
        cb_v = ttk.Combobox(action_frame, textvariable=target_var, width=22, state="readonly")
        btn_multi = tk.Button(action_frame, text="⚙ Multi Config", bg="#34495e", fg="white", width=19, command=lambda p=prog: self.open_multi_drums_config(p))

        tk.Label(f, text="Oct:", fg="#aaa", bg=row_bg).pack(side="left", padx=(5,0))
        sp_oct = tk.Spinbox(f, from_=-4, to=4, textvariable=oct_var, width=3, bg="#333", fg="#56dbff", command=self.update_live_mapping)
        sp_oct.pack(side="left", padx=2)

        tk.Label(f, text="Semi:", fg="#aaa", bg=row_bg).pack(side="left", padx=(5,0))
        sp_semi = tk.Spinbox(f, from_=-12, to=12, textvariable=semi_var, width=3, bg="#333", fg="#56dbff", command=self.update_live_mapping)
        sp_semi.pack(side="left", padx=2)

        tk.Label(f, text="Vol%:", fg="#aaa", bg=row_bg).pack(side="left", padx=(5,0))
        tk.Spinbox(f, from_=0, to=400, increment=5, textvariable=vol_var, width=4, bg="#333", fg="white").pack(side="left", padx=2)

        tk.Label(f, text="K:", fg="#aaa", bg=row_bg).pack(side="left", padx=(5,0))
        tk.Spinbox(f, from_=0, to=127, textvariable=key_var, width=3, bg="#333", fg="yellow").pack(side="left", padx=2)

        tk.Button(f, text="▶", bg="#8e44ad", fg="white", command=lambda p=prog, k=key_var: self.play_sf2_note(p, k.get())).pack(side="left", padx=5)

        def upd(e=None):
            mode = t_var.get()
            is_drum = (mode == "Drum")
            is_multi = (mode == "Multi")
            num_pitches = len(self.program_notes.get(prog, []))
            current_row_color = "#5c1a1a" if is_drum and num_pitches > 1 else "#222"
            f.config(bg=current_row_color)
            action_frame.config(bg=current_row_color)
            for child in f.winfo_children():
                if isinstance(child, (tk.Label, tk.Frame)): child.config(bg=current_row_color)
            if is_multi:
                cb_v.pack_forget(); btn_multi.pack(side="left")
                state = "disabled"
            else:
                btn_multi.pack_forget(); cb_v.pack(side="left")
                cb_v['values'] = GM_DRUMS_LIST if is_drum else GM_INST_LIST
                if target_var.get() not in cb_v['values']:
                    cb_v.current(prog if not is_drum and prog < len(GM_INST_LIST) else 0)
                state = "disabled" if is_drum else "normal"
            sp_oct.config(state=state); sp_semi.config(state=state); btn_t.config(state=state)
            self.update_live_mapping()

        cb_t.bind("<<ComboboxSelected>>", upd); upd()
        self.rows[prog] = {
            'type': t_var, 'target': target_var, 'solo': s_var, 'mute': m_var, 'tuning': t_var_tune,
            'vol': vol_var, 'key': key_var, 'octave': oct_var, 'semitone': semi_var,
            'btn_s': btn_s, 'btn_m': btn_m, 'btn_t': btn_t, 'cb_v': cb_v, 'sp_oct': sp_oct, 'sp_semi': sp_semi,
            'frame': f, 'action_frame': action_frame, 'upd_func': upd
        }
        if prog not in self.live_mapping: self.live_mapping[prog] = {'multi_drums': {}}
        self.update_live_mapping()

    def open_multi_drums_config(self, prog):
        top = tk.Toplevel(self)
        top.title(f"Multi Drums (P:{prog})")
        top.geometry("450x500")
        top.transient(self); top.config(bg="#1a1a1a")
        tk.Label(top, text="Pitch Assignment:", bg="#1a1a1a", fg="white", font=("Arial", 10, "bold")).pack(pady=10)
        container = tk.Frame(top, bg="#1a1a1a"); container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        cv = tk.Canvas(container, bg="#222", highlightthickness=0)
        sb = ttk.Scrollbar(container, orient="vertical", command=cv.yview)
        sf = tk.Frame(cv, bg="#222")
        sf.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.create_window((0, 0), window=sf, anchor="nw")
        cv.configure(yscrollcommand=sb.set)
        cv.pack(side="left", fill="both", expand=True); sb.pack(side="right", fill="y")
        used_notes = sorted(list(self.program_notes.get(prog, [])))
        for note in used_notes:
            rf = tk.Frame(sf, bg="#222"); rf.pack(fill=tk.X, pady=4, padx=5)
            tk.Label(rf, text=f"Pitch {note}", width=10, bg="#222", fg="white").pack(side=tk.LEFT)
            
            tk.Button(rf, text="🎵", bg="#8e44ad", fg="white", command=lambda n=note: self.play_sf2_note(prog, n)).pack(side=tk.LEFT, padx=5)
            opciones = ["(Keep original)"] + GM_DRUMS_LIST
            combo_drum = ttk.Combobox(rf, values=opciones, state="readonly", width=25)
            combo_drum.pack(side=tk.LEFT, padx=5)
            mapped_val = self.live_mapping[prog]['multi_drums'].get(str(note), "(Keep original)")
            combo_drum.set(mapped_val if mapped_val in opciones else "(Keep original)")
            combo_drum.bind("<<ComboboxSelected>>", lambda e, n=note, cb=combo_drum: self._save_multi_val(prog, n, cb.get()))

    def _save_multi_val(self, prog, note, val):
        self.live_mapping[prog]['multi_drums'][str(note)] = val

    def play_sf2_note(self, orig_program, note):
        if not self.synth or not self.sfid: return
        self.synth.program_select(0, self.sfid, 0, orig_program)
        self.synth.noteon(0, note, 100)
        self.after(800, lambda: self.synth.noteoff(0, note))

    def toggle_playback(self):
        if not self.synth or not self.sfid: return messagebox.showwarning("Warning", "SF2 not loaded.")
        if not self.midi_path: return messagebox.showwarning("Warning", "MIDI not loaded.")
        self.update_live_mapping()
        if self.is_playing: self.stop_playback()
        else: self.start_playback()

    def start_playback(self):
        self.is_playing = True
        self.btn_play.config(text="■ STOP PLAYBACK", bg="#c0392b")
        self.play_thread = threading.Thread(target=self._play_midi_loop, daemon=True)
        self.play_thread.start()

    def stop_playback(self):
        self.is_playing = False
        self.btn_play.config(text="▶ PLAY ORIGINAL", bg="#9b59b6")
        if self.synth:
            for ch in range(16): self.synth.cc(ch, 120, 0); self.synth.cc(ch, 123, 0)

    def _send_to_orig_synth(self, msg):
        if getattr(msg, 'channel', -1) == 15: return 
        if msg.type == 'program_change':
            bank = 128 if msg.channel == 9 else 0
            self.synth.program_select(msg.channel, self.sfid, bank, msg.program)
        elif msg.type == 'control_change': self.synth.cc(msg.channel, msg.control, msg.value)
        elif msg.type == 'pitchwheel': self.synth.pitch_bend(msg.channel, msg.pitch)

    def _play_midi_loop(self):
        try:
            target_start_time = float(self.start_time_var.get())
            current_time = 0.0
            active_program = {ch: 0 for ch in range(16)}
            playing_notes_orig = set(); playing_notes_tune = {}
            if self.sfid_tune: self.synth.program_select(15, self.sfid_tune, 0, 0)
            for msg in mido.MidiFile(self.midi_path):
                if not self.is_playing: break
                current_time += msg.time
                if hasattr(msg, 'channel') and msg.type == 'program_change': active_program[msg.channel] = msg.program
                if current_time < target_start_time:
                    if hasattr(msg, 'channel') and msg.type not in ['note_on', 'note_off']: self._send_to_orig_synth(msg)
                    continue
                sleep_time = msg.time
                if current_time - msg.time < target_start_time: sleep_time = current_time - target_start_time
                if sleep_time > 0:
                    waited = 0.0
                    while waited < sleep_time and self.is_playing:
                        chunk = min(0.02, sleep_time - waited)
                        time.sleep(chunk); waited += chunk
                if not self.is_playing: break
                if hasattr(msg, 'channel'):
                    prog = active_program.get(msg.channel, 0)
                    m = self.live_mapping.get(prog, {'type': 'inst', 'solo': False, 'mute': False, 'tuning': False, 'transpose': 0})
                    if msg.type in ['note_on', 'note_off']:
                        is_note_on = (msg.type == 'note_on' and msg.velocity > 0)
                        if is_note_on:
                            if not ((self.any_solo and not m['solo']) or (not self.any_solo and m['mute'])):
                                if m['type'] == 'drum':
                                    try: dp = int(m['target'].split(':')[0])
                                    except: dp = msg.note
                                    playing_notes_orig.add((9, dp)); self.synth.noteon(9, dp, msg.velocity)
                                elif m['type'] == 'multi':
                                    mapped_str = m.get('multi_drums', {}).get(str(msg.note), "")
                                    if mapped_str and mapped_str != "(Keep original)":
                                        dp = int(mapped_str.split(':')[0])
                                        playing_notes_orig.add((9, dp)); self.synth.noteon(9, dp, msg.velocity)
                                    else:
                                        playing_notes_orig.add((msg.channel, msg.note)); self.synth.noteon(msg.channel, msg.note, msg.velocity)
                                else:
                                    playing_notes_orig.add((msg.channel, msg.note)); self.synth.noteon(msg.channel, msg.note, msg.velocity)
                            if m['tuning'] and self.sfid_tune and m['type'] == 'inst':
                                tn = clamp(msg.note + m['transpose']); playing_notes_tune[(msg.channel, msg.note)] = tn; self.synth.noteon(15, tn, 100) 
                        else:
                            if m['type'] == 'drum':
                                try: dp = int(m['target'].split(':')[0])
                                except: dp = msg.note
                                if (9, dp) in playing_notes_orig: playing_notes_orig.remove((9, dp)); self.synth.noteoff(9, dp)
                            elif m['type'] == 'multi':
                                ms = m.get('multi_drums', {}).get(str(msg.note), "")
                                if ms and ms != "(Keep original)":
                                    dp = int(ms.split(':')[0])
                                    if (9, dp) in playing_notes_orig: playing_notes_orig.remove((9, dp)); self.synth.noteoff(9, dp)
                                else:
                                    if (msg.channel, msg.note) in playing_notes_orig: playing_notes_orig.remove((msg.channel, msg.note)); self.synth.noteoff(msg.channel, msg.note)
                            else:
                                if (msg.channel, msg.note) in playing_notes_orig: playing_notes_orig.remove((msg.channel, msg.note)); self.synth.noteoff(msg.channel, msg.note)
                            if (msg.channel, msg.note) in playing_notes_tune:
                                tn = playing_notes_tune.pop((msg.channel, msg.note)); self.synth.noteoff(15, tn)
                    else: self._send_to_orig_synth(msg)
        except: pass
        finally:
            self.is_playing = False; self.after(0, lambda: self.btn_play.config(text="▶ PLAY ORIGINAL", bg="#9b59b6")); self.stop_playback()

    def on_close(self):
        self.stop_playback()
        if self.synth: self.synth.delete()
        self.destroy()

    def get_mapping(self):
        mapping = {}
        for prog, v in self.rows.items():
            t_val = v['target'].get()
            mapping[prog] = {
                'type': v['type'].get().lower(), 
                'val': int(t_val.split(':')[0]) if ':' in t_val else 0,
                'solo': v['solo'].get(), 'mute': v['mute'].get(), 'tuning': v['tuning'].get(),
                'vol_mult': v['vol'].get(), 'transpose': (v['octave'].get() * 12) + v['semitone'].get(),
                'multi_drums': self.live_mapping.get(prog, {}).get('multi_drums', {})
            }
        return mapping

    def save_config(self):
        if not self.config_path: return
        data = {str(k): {'type': v['type'].get(), 'val_str': v['target'].get(), 'solo': v['solo'].get(), 'mute': v['mute'].get(), 'tuning': v['tuning'].get(), 'vol': v['vol'].get(), 'key': v['key'].get(), 'oct': v['octave'].get(), 'semi': v['semitone'].get(), 'multi_drums': self.live_mapping.get(k, {}).get('multi_drums', {})} for k, v in self.rows.items()}
        with open(self.config_path, 'w') as f: json.dump(data, f, indent=4)
        messagebox.showinfo("OK", "Configuration saved.")

    def load_config(self):
        if not self.config_path or not os.path.exists(self.config_path): return
        try:
            with open(self.config_path, 'r') as f: data = json.load(f)
            for prog, v in self.rows.items():
                if str(prog) in data:
                    c = data[str(prog)]
                    v['type'].set(c.get('type', 'Inst')); v['octave'].set(c.get('oct', 0)); v['semitone'].set(c.get('semi', 0))
                    v['vol'].set(c.get('vol', 100)); v['key'].set(c.get('key', 60)); v['target'].set(c.get('val_str', ""))
                    v['solo'].set(c.get('solo', False)); v['mute'].set(c.get('mute', False)); v['tuning'].set(c.get('tuning', False))
                    v['btn_s'].config(bg="#E6DB74" if v['solo'].get() else "#444", fg="black" if v['solo'].get() else "white")
                    v['btn_m'].config(bg="#F92672" if v['mute'].get() else "#444")
                    v['btn_t'].config(bg="#3498db" if v['tuning'].get() else "#444")
                    self.live_mapping[prog]['multi_drums'] = c.get('multi_drums', {})
                    v['upd_func']()
            self.update_live_mapping()
        except: pass

    def process_midi_logic(self):
        mapping = self.get_mapping()
        any_solo = any(m['solo'] for m in mapping.values())
        new_midi = mido.MidiFile(type=1, ticks_per_beat=self.midi.ticks_per_beat)
        active_notes_tracker = {}

        def to_delta_track(abs_events, name):
            abs_events.sort(key=lambda x: x[0]); t = mido.MidiTrack(); t.append(mido.MetaMessage('track_name', name=name, time=0))
            last_time = 0
            for abs_time, msg in abs_events:
                t.append(msg.copy(time=abs_time - last_time)); last_time = abs_time
            return t

        tempo_events = []
        for track_idx, track in enumerate(self.midi.tracks):
            abs_time = 0; abs_events = []
            for msg in track: abs_time += msg.time; abs_events.append((abs_time, msg))
            inst_events, drum_events = [], []; has_inst_notes, has_drum_notes = False, False
            active_program = {ch: 0 for ch in range(16)}

            for cur_time, msg in abs_events:
                if msg.is_meta:
                    if msg.type in ['set_tempo', 'time_signature'] and track_idx == 0: tempo_events.append((cur_time, msg))
                    else: inst_events.append((cur_time, msg)); drum_events.append((cur_time, msg))
                    continue
                if hasattr(msg, 'channel'):
                    ch = msg.channel
                    if msg.type == 'program_change': active_program[ch] = msg.program
                    if msg.type in ['note_on', 'note_off']:
                        is_note_on = (msg.type == 'note_on' and msg.velocity > 0); note_key = (ch, msg.note)
                        if is_note_on:
                            prog = active_program[ch]
                            m = mapping.get(prog, {'type': 'inst', 'val': prog, 'solo': False, 'mute': False, 'vol_mult': 100, 'transpose': 0})
                            if (any_solo and not m['solo']) or (not any_solo and m['mute']): continue
                            new_vel = clamp(msg.velocity * (m['vol_mult'] / 100.0))
                            if m['type'] == 'drum':
                                new_msg = msg.copy(channel=9, note=m['val'], velocity=new_vel)
                                drum_events.append((cur_time, new_msg)); has_drum_notes = True
                                active_notes_tracker[note_key] = (9, new_msg.note, 'drum')
                            elif m['type'] == 'multi':
                                ms = m.get('multi_drums', {}).get(str(msg.note), "")
                                if ms and ms != "(Keep original)":
                                    dv = int(ms.split(':')[0]); new_msg = msg.copy(channel=9, note=dv, velocity=new_vel)
                                    drum_events.append((cur_time, new_msg)); has_drum_notes = True
                                    active_notes_tracker[note_key] = (9, new_msg.note, 'drum')
                                else:
                                    new_msg = msg.copy(channel=ch, note=clamp(msg.note + m['transpose']), velocity=new_vel)
                                    inst_events.append((cur_time, new_msg)); has_inst_notes = True
                                    active_notes_tracker[note_key] = (ch, new_msg.note, 'inst')
                            else:
                                new_msg = msg.copy(channel=ch, note=clamp(msg.note + m['transpose']), velocity=new_vel)
                                inst_events.append((cur_time, new_msg)); has_inst_notes = True
                                active_notes_tracker[note_key] = (ch, new_msg.note, 'inst')
                        else:
                            if note_key in active_notes_tracker:
                                tc, tn, tt = active_notes_tracker.pop(note_key); om = msg.copy(channel=tc, note=tn)
                                if tt == 'drum': drum_events.append((cur_time, om))
                                else: inst_events.append((cur_time, om))
                    else:
                        prog = active_program[ch]
                        m = mapping.get(prog, {'solo': False, 'mute': False})
                        if (any_solo and not m['solo']) or (not any_solo and m['mute']): continue
                        if msg.type == 'program_change':
                            mp = mapping.get(msg.program, {'type': 'inst', 'val': msg.program})
                            if mp['type'] == 'inst': inst_events.append((cur_time, msg.copy(program=mp['val'])))
                        else: inst_events.append((cur_time, msg.copy())); drum_events.append((cur_time, msg.copy(channel=9)))

            if track_idx == 0 and tempo_events: new_midi.tracks.append(to_delta_track(tempo_events, "Tempo"))
            if has_inst_notes: new_midi.tracks.append(to_delta_track(inst_events, f"Trk {track_idx} Inst"))
            if has_drum_notes: new_midi.tracks.append(to_delta_track(drum_events, f"Trk {track_idx} Drums"))
        return new_midi

    def preview_midi(self):
        if not self.midi: return
        out_path = os.path.join(tempfile.gettempdir(), "preview_temp.mid")
        self.process_midi_logic().save(out_path)
        if platform.system() == 'Windows': os.startfile(out_path)
        else: subprocess.call(['open' if platform.system() == 'Darwin' else 'xdg-open', out_path])

    def export_midi(self):
        if not self.midi: return
        path = filedialog.asksaveasfilename(defaultextension=".mid", filetypes=[("MIDI files", "*.mid")])
        if path: self.process_midi_logic().save(path); messagebox.showinfo("Success", "Exported.")

if __name__ == "__main__":
    root = TkinterDnD.Tk(); root.withdraw()
    app = AdvancedMidiEditor(root)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()