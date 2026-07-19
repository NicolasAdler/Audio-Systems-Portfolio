# BLOCK 1 START
import tkinter as tk
from tkinter import filedialog
import math
import copy
from TS_Parameters import TS_Parameters
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Global state management
entries_matrix = []      # List of dicts mapping labels to Entry widgets per system
ts_objects = []          # List of TS_Parameters instances
user_inputs = []         # List of dicts tracking manual entry flags (True/False)
autocalc_buttons = []    # List of Auto-Calculate Button widgets
driver_count_vars = []   # List of StringVar tracking driver counts per system column

# Global tracking variables for the secondary window
plot_window = None
canvas = None
ax = None
hover_annotation = None

# Global configuration variables
labels = [
    "Vas", "fs", "Qts", "Qes", "Qms", "Xmax", "Sd", 
    "Sensitivity", "Re", "n0", "Cms", "Mms", "Rms", "Bl", 
    "Box Volume", "Power"
]

units = {
    "Vas": "liters", "fs": "Hz", "Qts": "", "Qes": "", "Qms": "",
    "Xmax": "mm", "Sd": "cm²", "Sensitivity": "dB", "Re": "Ohms",
    "n0": "", "Cms": "mm/N", "Mms": "g", "Rms": "kg/s",
    "Bl": "T*m", "Box Volume": "liters", "Power": "Watts"
}

def map_label_to_attr(label):
    """Maps UI display labels directly to TS_Parameters class attribute strings."""
    return {
        "Vas": "Vas", "fs": "fs", "Qts": "Qts", "Qes": "Qes", "Qms": "Qms",
        "Xmax": "Xmax", "Sd": "Sd", "Sensitivity": "Sensitivity", "Re": "Re",
        "n0": "n0", "Cms": "Cms", "Mms": "Mms", "Rms": "Rms", "Bl": "Bl",
        "Box Volume": "Vb", "Power": "W"
    }.get(label)

def can_system_solve(system_index):
    """Simulates calculation to check if current inputs resolve any empty fields."""
    if system_index >= len(ts_objects):
        return False
        
    ts_copy = copy.deepcopy(ts_objects[system_index])
    ts_copy.solve()
    
    for label_text in labels:
        attr_name = map_label_to_attr(label_text)
        if attr_name and hasattr(ts_copy, attr_name):
            calculated_val = getattr(ts_copy, attr_name)
            if calculated_val != 0.0 and calculated_val is not None:
                entry = entries_matrix[system_index][label_text]
                if entry.get().strip() == "":
                    return True
    return False

def update_button_state(system_index):
    """Updates the target button's state and color based on solve potential."""
    if system_index >= len(autocalc_buttons):
        return
        
    button = autocalc_buttons[system_index]
    if can_system_solve(system_index):
        button.config(state="normal", bg="lightgreen", activebackground="darkgreen")
    else:
        default_bg = "SystemButtonFace" if tk.TkVersion >= 8.5 else "lightgray"
        button.config(state="disabled", bg=default_bg)

# BLOCK 1 END

#BLOCK 2 START
def update_ts_value(system_index, label):
    """Handles real-time value validation and synchronizes UI input with the backend model."""
    entry = entries_matrix[system_index][label]
    ts = ts_objects[system_index]
    text = entry.get().strip()
    
    if text == "":
        user_inputs[system_index][label] = False
        attr_name = map_label_to_attr(label)
        if attr_name and hasattr(ts, attr_name):
            setattr(ts, attr_name, 0.0)
        update_button_state(system_index)
        return
        
    try:
        value = float(text)
        user_inputs[system_index][label] = True
    except ValueError:
        return

    # Assign value to TS class instance using dedicated setter methods
    if label == "Vas": ts.set_Vas(Vas=value)
    elif label == "fs": ts.set_fs(fs=value)
    elif label == "Qts": ts.set_Qts(Qts=value)
    elif label == "Qes": ts.set_Qes(Qes=value)
    elif label == "Qms": ts.set_Qms(Qms=value)
    elif label == "Mms": ts.set_Mms(Mms=value)
    elif label == "Cms": ts.set_Cms(value)
    elif label == "Sd": ts.set_Sd(value)
    elif label == "Xmax": ts.set_Xmax(Xmax=value)
    elif label == "Re": ts.set_Re(value)
    elif label == "Rms": ts.set_Rms(Rms=value)
    elif label == "n0": ts.set_n0(n0=value)
    elif label == "Bl": ts.set_Bl(value)
    elif label == "Box Volume": ts.set_Vb(value)
    elif label == "Power": ts.set_W(value)

    update_button_state(system_index)

def auto_calculate(system_index):
    """Executes backend math engine updates and pushes solved values directly into blank UI fields."""
    ts = ts_objects[system_index]
    ts.solve()
    
    for label_text in labels:
        attr_name = map_label_to_attr(label_text)
        if attr_name and hasattr(ts, attr_name):
            val = getattr(ts, attr_name)
            if val != 0.0 and val is not None:
                entry = entries_matrix[system_index][label_text]
                if entry.get().strip() == "":
                    entry.insert(0, f"{val:.4f}")
                    user_inputs[system_index][label_text] = True

    update_button_state(system_index)

def load_file(system_index):
    """Parses whitespace-separated parameters from external text files into specified data structures."""
    file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
    if not file_path:
        return
        
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) < 2:
                continue
                
            value_str = parts[-1]
            parameter_name = " ".join(parts[:-1])
            
            try:
                float(value_str)
            except ValueError:
                continue

            for label_text in labels:
                attr_name = map_label_to_attr(label_text)
                if label_text.lower() == parameter_name.lower() or (attr_name and attr_name.lower() == parameter_name.lower()):
                    entry = entries_matrix[system_index][label_text]
                    entry.delete(0, tk.END)
                    entry.insert(0, value_str)
                    update_ts_value(system_index, label_text)
                    break

# BLOCK 2 END

# BLOCK 3 START
def compute_transfer_function(ts, driver_count):
    """
    Computes acoustic output for N drivers in a single shared enclosure volume.
    Each driver sees an effective volume of (Vb / N) and an effective power of (W / N).
    """
    if hasattr(ts, 'Vb') and hasattr(ts, 'W'):
        if 0.0 in [ts.n0, ts.fs, ts.Qts, ts.Vas, ts.Vb, ts.W] or any(v is None for v in [ts.n0, ts.fs, ts.Qts, ts.Vas, ts.Vb, ts.W]):
            return None, None
        
        effective_Vb = ts.Vb / driver_count
        effective_W = ts.W / driver_count
    else:
        return None, None

    freqs = []
    spl = []

    # Calculate baseline single driver criteria
    SPL_ref = 112.2 + 10 * math.log10(ts.n0)
    W_gain = 10 * math.log10(effective_W)

    for i in range(20001):
        f = float(i)
        freqs.append(f)

        if f < 1.0:
            spl.append(0.0)
            continue

        freq_ratio = f / ts.fs
        sys_stiffness = (ts.Vas / effective_Vb) + 1.0

        Hf_top = freq_ratio ** 2
        Hf_bottom_1 = (sys_stiffness - Hf_top) ** 2
        Hf_bottom_2 = (freq_ratio / ts.Qts) ** 2

        denominator = Hf_bottom_1 + Hf_bottom_2
        if denominator <= 0.0:
            spl.append(0.0)
            continue

        Hf = Hf_top / math.sqrt(denominator)
        
        if Hf == 0.0:
            single_driver_spl = 0.0
        else:
            single_driver_spl = (SPL_ref + 20 * math.log10(abs(Hf))) + W_gain
            
        # Account for acoustic coupling gain output additions (+10 * log10(N))
        total_system_spl = single_driver_spl + (10 * math.log10(driver_count))
        spl.append(total_system_spl)

    return freqs, spl

def create_plot_window():
    """Initializes or restores an independent window container for the Matplotlib chart."""
    global plot_window, canvas, ax, hover_annotation
    
    if plot_window is not None and tk.Toplevel.winfo_exists(plot_window):
        plot_window.lift()
        return

    plot_window = tk.Toplevel(window)
    plot_window.title("Acoustic Response Monitor")
    plot_window.geometry("800x600")
    plot_window.minsize(500, 400)
    
    fig = Figure(figsize=(8, 6), dpi=100)
    ax = fig.add_subplot(111)
    
    ax.set_title("Transfer Function Comparison")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("SPL (dB)")
    ax.set_xscale("log")
    ax.set_xlim(20, 20000)
    ax.set_ylim(75, 110)
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)

    # Initialize transparent tooltip popup label overlay container properties
    hover_annotation = ax.annotate(
        "", xy=(0,0), xytext=(15,15), textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.9, lw=1),
        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0")
    )
    hover_annotation.set_visible(False)

    def on_mouse_hover(event):
        """Tracks the mouse paths across canvas limits and generates hover pop-ups."""
        if event.inaxes != ax:
            return

        visible = hover_annotation.get_visible()
        hovered_any_line = False

        for line in ax.get_lines():
            if line.get_label().startswith("_"):
                continue

            contained, info = line.contains(event)
            if contained:
                hovered_any_line = True
                
                # Extract coordinates from target index mapping arrays
                x_data, y_data = line.get_data()
                ind = info['ind'][0]
                target_x = x_data[ind]
                target_y = y_data[ind]

                # Adjust location anchoring markers
                hover_annotation.xy = (target_x, target_y)
                
                system_name = line.get_label()
                hover_annotation.set_text(f"{system_name}\nFreq: {target_x:.1f} Hz\nSPL: {target_y:.2f} dB")
                
                # Match popup backdrop frame border profile to its line asset color
                hover_annotation.get_bbox_patch().set_edgecolor(line.get_color())
                hover_annotation.set_visible(True)
                canvas.draw_idle()
                break

        if not hovered_any_line and visible:
            hover_annotation.set_visible(False)
            canvas.draw_idle()

    canvas = FigureCanvasTkAgg(fig, master=plot_window)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Establish link hooks directly into Matplotlib runtime cycle updates
    fig.canvas.mpl_connect("motion_notify_event", on_mouse_hover)
    canvas.draw()

def generate_plot():
    """Refreshes the external Matplotlib window axes with new speaker simulation curves."""
    global ax, canvas, hover_annotation
    create_plot_window()
    
    if hover_annotation is not None:
        hover_annotation.set_visible(False)
        
    ax.clear()

    # Re-establish overlay elements to avoid garbage collection on clearing
    hover_annotation = ax.annotate(
        "", xy=(0,0), xytext=(15,15), textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.9, lw=1),
        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0")
    )
    hover_annotation.set_visible(False)

    for i, ts in enumerate(ts_objects):
        ts.solve()
        try:
            count = int(driver_count_vars[i].get())
        except (IndexError, ValueError):
            count = 1
            
        freqs, spl = compute_transfer_function(ts, count)
        if freqs is None:
            continue
            
        label_suffix = f" ({count} Drivers)" if count > 1 else " (Single)"
        # Set picker tolerance radius parameter here (5 pixels) to ease mouse focus matching
        ax.plot(freqs, spl, label=f"System {i+1}{label_suffix}", picker=5)

    ax.set_title("Transfer Function Comparison")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("SPL (dB)")
    ax.set_xscale("log")
    ax.set_xlim(20, 20000)
    ax.set_ylim(75, 110)
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)
    if ax.get_legend_handles_labels():
        ax.legend()
    canvas.draw()

def clear_graph():
    """Wipes plotted metrics from the external coordinate viewer workspace."""
    global ax, canvas, hover_annotation
    if plot_window is None or not tk.Toplevel.winfo_exists(plot_window):
        return
    ax.clear()
    
    hover_annotation = ax.annotate(
        "", xy=(0,0), xytext=(15,15), textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.5", fc="white", alpha=0.9, lw=1),
        arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0")
    )
    hover_annotation.set_visible(False)
    
    ax.set_title("Transfer Function Comparison")
    ax.set_xlabel("Frequency (Hz)")
    ax.set_ylabel("SPL (dB)")
    ax.set_xscale("log")
    ax.set_xlim(20, 20000)
    ax.set_ylim(75, 110)
    ax.grid(True, which="both", linestyle="--", linewidth=0.5)
    canvas.draw()

#BLOCK 3 END

# BLOCK 4 START

def update_fields(*args):
    """Dynamically rebuilds UI grid with data persistence, auto-resize bounds, and arrow scalers."""
    for widget in entry_frame.winfo_children():
        widget.destroy()

    try:
        num_systems = int(selection_var.get())
    except (ValueError, NameError):
        num_systems = 1

    global entries_matrix, ts_objects, user_inputs, autocalc_buttons, driver_count_vars
    old_ts_objects, old_user_inputs, old_driver_vars = ts_objects, user_inputs, driver_count_vars
    
    ts_objects, user_inputs, autocalc_buttons, driver_count_vars = [], [], [], []
    
    for i in range(num_systems):
        if i < len(old_ts_objects):
            ts_objects.append(old_ts_objects[i])
            user_inputs.append(old_user_inputs[i])
            driver_count_vars.append(old_driver_vars[i])
        else:
            ts_objects.append(TS_Parameters())
            user_inputs.append({})
            driver_count_vars.append(tk.StringVar(value="1"))

    entries_matrix = [{} for _ in range(num_systems)]

    # Assign scaling weight configurations across the active column sets
    entry_frame.columnconfigure(0, weight=1)
    for col in range(num_systems):
        entry_frame.columnconfigure(col + 1, weight=2)
    entry_frame.columnconfigure(num_systems + 1, weight=1)

    for col in range(num_systems):
        tk.Label(entry_frame, text=f"System {col+1}", font=('Arial', 10, 'bold')).grid(row=0, column=col+1, sticky="nsew")

    tk.Label(entry_frame, text="Driver Count", font=('Arial', 9, 'italic')).grid(row=1, column=0, sticky="e")
    for c in range(num_systems):
        count_menu = tk.OptionMenu(entry_frame, driver_count_vars[c], "1", "2", "3", "4", "6", "8")
        count_menu.config(width=5)
        count_menu.grid(row=1, column=c+1, padx=4, pady=2, sticky="ew")

    for r, label_text in enumerate(labels):
        grid_row = r + 2
        entry_frame.rowconfigure(grid_row, weight=1)
        
        tk.Label(entry_frame, text=label_text).grid(row=grid_row, column=0, sticky="e", padx=(5, 2))
        tk.Label(entry_frame, text=units.get(label_text, "")).grid(row=grid_row, column=num_systems+1, sticky="w", padx=(2, 5))

        for c in range(num_systems):
            entry = tk.Entry(entry_frame, width=10)
            entry.grid(row=grid_row, column=c+1, padx=4, pady=2, sticky="ew")
            
            attr_name = map_label_to_attr(label_text)
            if attr_name and hasattr(ts_objects[c], attr_name):
                val = getattr(ts_objects[c], attr_name)
                if val != 0.0 and val is not None:
                    entry.insert(0, str(int(val)) if val == int(val) else f"{val:.4f}".rstrip('0').rstrip('.'))

            def handle_arrow_scaling(event, col=c, label=label_text, entry_widget=entry):
                text_val = entry_widget.get().strip()
                if not text_val: return
                try: current_val = float(text_val)
                except ValueError: return

                step = 0.01 if label in ["Qts", "Qes", "Qms", "n0"] else 0.1 if label in ["Cms", "Rms", "Xmax"] else 1.0 if label in ["fs", "Bl", "Power", "Box Volume"] else 0.5
                new_val = current_val + step if event.keysym == "Up" else max(0.0, current_val - step)

                entry_widget.delete(0, tk.END)
                entry_widget.insert(0, str(int(new_val)) if new_val == int(new_val) else f"{new_val:.4f}".rstrip('0').rstrip('.'))
                update_ts_value(col, label)
                generate_plot()

            entry.bind("<KeyRelease>", lambda e, col=c, label=label_text: update_ts_value(col, label))
            entry.bind("<Up>", handle_arrow_scaling)
            entry.bind("<Down>", handle_arrow_scaling)
            entries_matrix[c][label_text] = entry

    button_row = len(labels) + 2
    entry_frame.rowconfigure(button_row, weight=1)
    entry_frame.rowconfigure(button_row+1, weight=1)
    entry_frame.rowconfigure(button_row+2, weight=1)
    entry_frame.rowconfigure(button_row+3, weight=1)

    for c in range(num_systems):
        tk.Button(entry_frame, text="Load File", command=lambda idx=c: load_file(idx), bg="lightgray", width=15).grid(row=button_row, column=c+1, pady=4, padx=2, sticky="ew")
    for c in range(num_systems):
        btn = tk.Button(entry_frame, text="Auto Calculate", state="disabled", command=lambda idx=c: auto_calculate(idx), width=15)
        btn.grid(row=button_row+1, column=c+1, pady=4, padx=2, sticky="ew")
        autocalc_buttons.append(btn)
        update_button_state(c)

    tk.Button(entry_frame, text="Generate Plot", command=generate_plot, bg="lightblue", width=20).grid(row=button_row+2, column=1, columnspan=num_systems, pady=6, sticky="ew")
    tk.Button(entry_frame, text="Clear Graph", command=clear_graph, bg="lightcoral", width=20).grid(row=button_row+3, column=1, columnspan=num_systems, pady=4, sticky="ew")

    # Resize main console width window coordinates automatically based on active workspace columns
    calculated_width = 180 + (num_systems * 110) + 80
    window.geometry(f"{calculated_width}x680")

# --- Main Window Frame Setup ---
window = tk.Tk()
window.title("TS Parameter Console")
window.geometry("400x680")
window.minsize(350, 600)

top_frame = tk.Frame(window)
top_frame.pack(side="top", fill="x", pady=10)

tk.Label(top_frame, text="Select Number of Systems: ", font=('Arial', 10)).pack(side="left", padx=(20, 5))
selection_var = tk.StringVar(value="1")
dropdown = tk.OptionMenu(top_frame, selection_var, "1", "2", "3", "4")
dropdown.pack(side="left")

if hasattr(selection_var, 'trace_add'): selection_var.trace_add("write", update_fields)
else: selection_var.trace("w", update_fields)

entry_frame = tk.Frame(window, relief="groove", borderwidth=1)
entry_frame.pack(side="top", padx=15, pady=10, fill="both", expand=True)

update_fields()
create_plot_window()
window.mainloop()

# BLOCK 4 END
